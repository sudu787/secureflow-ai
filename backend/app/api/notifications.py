"""Notifications API — In-app notification management."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.notification import Notification

router = APIRouter()


@router.get("")
async def list_notifications(limit: int = 50, db: Session = Depends(get_db)):
    """List notifications, most recent first."""
    notifs = db.query(Notification).order_by(
        Notification.created_at.desc()
    ).limit(limit).all()

    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "severity": n.severity,
            "category": n.category,
            "is_read": n.is_read,
            "related_alert_id": n.related_alert_id,
            "related_incident_id": n.related_incident_id,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifs
    ]


@router.get("/unread-count")
async def unread_count(db: Session = Depends(get_db)):
    """Get count of unread notifications."""
    count = db.query(Notification).filter(Notification.is_read == False).count()
    return {"count": count}


@router.patch("/{notification_id}/read")
async def mark_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark a notification as read."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"status": "read", "id": notification_id}


@router.post("/mark-all-read")
async def mark_all_read(db: Session = Depends(get_db)):
    """Mark all notifications as read."""
    db.query(Notification).filter(Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"status": "all_read"}
