"""Audit Log model for security audit trail."""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, func
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False, index=True)  # login, query, prompt_injection_blocked, policy_violation, etc.
    resource_type = Column(String(50), nullable=True)  # alert, ticket, chat, etc.
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    severity = Column(String(20), default="info")  # info, warning, critical
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
