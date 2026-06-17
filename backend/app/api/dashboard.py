"""Dashboard API - Real-time stats and metrics."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.dashboard_service import (
    get_dashboard_stats, get_threat_trends, get_recent_alerts,
    get_agent_activity, get_system_health, get_top_attack_types,
    get_severity_distribution,
)

router = APIRouter()


@router.get("/stats")
async def dashboard_stats(db: Session = Depends(get_db)):
    return get_dashboard_stats(db)


@router.get("/threats")
async def threat_trends(hours: int = 24, db: Session = Depends(get_db)):
    return get_threat_trends(db, hours)


@router.get("/recent-alerts")
async def recent_alerts(limit: int = 10, db: Session = Depends(get_db)):
    return get_recent_alerts(db, limit)


@router.get("/agent-activity")
async def agent_activity(limit: int = 20, db: Session = Depends(get_db)):
    return get_agent_activity(db, limit)


@router.get("/system-health")
async def system_health():
    return get_system_health()


@router.get("/attack-types")
async def attack_types(db: Session = Depends(get_db)):
    return get_top_attack_types(db)


@router.get("/severity-distribution")
async def severity_distribution(db: Session = Depends(get_db)):
    return get_severity_distribution(db)


@router.get("/full")
async def full_dashboard(db: Session = Depends(get_db)):
    """Get complete dashboard data in one call."""
    return {
        "stats": get_dashboard_stats(db),
        "threat_trends": get_threat_trends(db),
        "recent_alerts": get_recent_alerts(db),
        "recent_agent_activity": get_agent_activity(db),
        "system_health": get_system_health(),
        "top_attack_types": get_top_attack_types(db),
        "severity_distribution": get_severity_distribution(db),
    }
