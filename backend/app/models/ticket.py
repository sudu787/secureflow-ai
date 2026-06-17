"""Ticket model for IT support and incident tickets."""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, func
from app.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)  # security_incident, vpn, email, printer, performance, account, software, other
    priority = Column(String(5), default="P3", index=True)  # P1, P2, P3, P4
    status = Column(String(30), default="open", index=True)  # open, in_progress, escalated, resolved, closed
    owner = Column(String(100), nullable=True)
    requester = Column(String(100), nullable=True)
    source = Column(String(50), default="manual")  # manual, ai_agent, automation
    related_incident_id = Column(Integer, nullable=True)
    related_alert_id = Column(Integer, nullable=True)
    diagnosis = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)
    escalation_reason = Column(Text, nullable=True)
    timeline = Column(JSON, nullable=True)  # [{timestamp, action, actor}]
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime, nullable=True)
