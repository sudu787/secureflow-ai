"""Pydantic schemas for dashboard."""

from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime


class DashboardStats(BaseModel):
    total_events: int = 0
    total_alerts: int = 0
    open_alerts: int = 0
    critical_alerts: int = 0
    high_alerts: int = 0
    medium_alerts: int = 0
    low_alerts: int = 0
    total_incidents: int = 0
    open_incidents: int = 0
    total_tickets: int = 0
    open_tickets: int = 0
    resolved_tickets: int = 0
    risk_score: float = 0.0
    risk_level: str = "low"
    agent_actions_today: int = 0
    false_positive_rate: float = 0.0
    mean_time_to_respond: Optional[float] = None  # minutes
    events_per_hour: float = 0.0


class ThreatTrend(BaseModel):
    timestamp: str
    count: int
    severity: str


class SystemHealthItem(BaseModel):
    service: str
    status: str  # healthy, degraded, down
    uptime: Optional[str] = None
    last_check: Optional[str] = None


class DashboardResponse(BaseModel):
    stats: DashboardStats
    threat_trends: List[ThreatTrend] = []
    recent_alerts: List[Any] = []
    recent_agent_activity: List[Any] = []
    system_health: List[SystemHealthItem] = []
    top_attack_types: List[Dict[str, Any]] = []
    severity_distribution: Dict[str, int] = {}
