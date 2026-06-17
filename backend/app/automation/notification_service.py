"""
SecureFlow AI — Notification Service
In-app notification system for alerts, tickets, and agent actions.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.notification import Notification

logger = logging.getLogger(__name__)


def create_notification(
    db: Session,
    title: str,
    message: str,
    severity: str = "info",
    category: str = "system",
    related_alert_id: int = None,
    related_incident_id: int = None,
) -> Optional[Notification]:
    """Create an in-app notification."""
    try:
        notif = Notification(
            title=title,
            message=message,
            severity=severity,
            category=category,
            related_alert_id=related_alert_id,
            related_incident_id=related_incident_id,
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        logger.info(f"🔔 Notification: [{severity}] {title}")
        return notif
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create notification: {e}")
        return None


def get_unread_count(db: Session) -> int:
    """Get count of unread notifications."""
    return db.query(Notification).filter(Notification.is_read == False).count()


def mark_as_read(db: Session, notification_id: int) -> bool:
    """Mark a notification as read."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if notif:
        notif.is_read = True
        db.commit()
        return True
    return False
