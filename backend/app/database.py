"""
SecureFlow AI - Database Configuration
SQLAlchemy engine, session management, and base model setup.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import os

# Ensure data directory exists
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite"):
    db_path = db_url.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    engine = create_engine(db_url, connect_args={"check_same_thread": False}, echo=False)
else:
    engine = create_engine(db_url, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    from app.models import user, event, alert, incident, ticket, agent_action, audit_log, chat_session  # noqa
    from app.models import notification  # noqa
    Base.metadata.create_all(bind=engine)
