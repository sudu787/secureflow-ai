"""Notification model for in-app alerts."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, func
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="info")  # info, warning, critical
    category = Column(String(50), default="system")  # system, alert, ticket, agent
    is_read = Column(Boolean, default=False, index=True)
    related_alert_id = Column(Integer, nullable=True)
    related_incident_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
