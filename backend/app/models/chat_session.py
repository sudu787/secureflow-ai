"""Chat Session model for AI conversation history."""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, func
from app.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_type = Column(String(50), default="general")  # general, security, it_support, investigation
    title = Column(String(500), default="New Conversation")
    messages = Column(JSON, default=list)  # [{role, content, timestamp, agent, metadata}]
    agent_used = Column(String(100), nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
