"""
SecureFlow AI - Memory Database Models
Defines SQLAlchemy models for Session Memory and Incident Memory.
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, func
from app.database import Base

class SessionMemory(Base):
    """Stores analyst session chat history and short-term working context."""
    __tablename__ = "session_memory"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)  # Tool outputs, intermediate states
    created_at = Column(DateTime, server_default=func.now(), index=True)

class IncidentMemory(Base):
    """Long-term organizational storage of resolved incidents and lessons learned."""
    __tablename__ = "incident_memory"

    id = Column(Integer, primary_key=True, index=True)
    original_alert_id = Column(Integer, nullable=True)
    title = Column(String(500), nullable=False)
    root_cause_summary = Column(Text, nullable=False)
    mitigation_applied = Column(Text, nullable=False)
    iocs = Column(JSON, nullable=True)  # List of IoCs
    vector_id = Column(String(100), nullable=True)  # Link to ChromaDB vector ID
    created_at = Column(DateTime, server_default=func.now(), index=True)
