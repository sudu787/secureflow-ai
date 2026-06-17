"""Incident model for grouped, investigated security incidents."""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, func
from app.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    status = Column(String(30), default="open", index=True)  # open, investigating, contained, resolved, closed
    priority = Column(String(5), default="P3")
    related_alert_ids = Column(JSON, nullable=True)  # [1, 2, 3]
    related_event_ids = Column(JSON, nullable=True)
    investigation_results = Column(JSON, nullable=True)  # structured investigation data
    root_cause = Column(Text, nullable=True)
    attack_path = Column(Text, nullable=True)
    affected_systems = Column(JSON, nullable=True)
    remediation_plan = Column(JSON, nullable=True)
    remediation_status = Column(String(30), default="pending")
    assigned_to = Column(String(100), nullable=True)
    executive_summary = Column(Text, nullable=True)
    technical_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime, nullable=True)
