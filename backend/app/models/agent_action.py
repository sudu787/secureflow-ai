"""Agent Action model for tracking all AI agent activities."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, func
from app.database import Base


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), nullable=False, index=True)  # triage, investigation, remediation, it_support, reporting
    action_type = Column(String(100), nullable=False)  # analyze, investigate, remediate, diagnose, report
    input_summary = Column(Text, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    output_summary = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    status = Column(String(30), default="completed")  # running, completed, failed
    duration_ms = Column(Integer, nullable=True)
    related_alert_id = Column(Integer, nullable=True)
    related_ticket_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
