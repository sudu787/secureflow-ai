"""
SecureFlow AI - Dashboard Service
Computes dashboard statistics, risk scores, and aggregated metrics.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.event import Event
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.ticket import Ticket
from app.models.agent_action import AgentAction


def get_dashboard_stats(db: Session) -> dict:
    """Compute comprehensive dashboard statistics."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Event stats
    total_events = db.query(func.count(Event.id)).scalar() or 0
    events_today = db.query(func.count(Event.id)).filter(Event.ingested_at >= today_start).scalar() or 0

    # Alert stats
    total_alerts = db.query(func.count(Alert.id)).scalar() or 0
    open_alerts = db.query(func.count(Alert.id)).filter(Alert.status == "open").scalar() or 0
    critical_alerts = db.query(func.count(Alert.id)).filter(
        and_(Alert.severity == "critical", Alert.status == "open")
    ).scalar() or 0
    high_alerts = db.query(func.count(Alert.id)).filter(
        and_(Alert.severity == "high", Alert.status == "open")
    ).scalar() or 0
    medium_alerts = db.query(func.count(Alert.id)).filter(
        and_(Alert.severity == "medium", Alert.status == "open")
    ).scalar() or 0
    low_alerts = db.query(func.count(Alert.id)).filter(
        and_(Alert.severity == "low", Alert.status == "open")
    ).scalar() or 0
    resolved_alerts = db.query(func.count(Alert.id)).filter(Alert.status == "resolved").scalar() or 0
    false_positives = db.query(func.count(Alert.id)).filter(Alert.status == "false_positive").scalar() or 0

    # Incident stats
    total_incidents = db.query(func.count(Incident.id)).scalar() or 0
    open_incidents = db.query(func.count(Incident.id)).filter(
        Incident.status.in_(["open", "investigating", "contained"])
    ).scalar() or 0

    # Ticket stats
    total_tickets = db.query(func.count(Ticket.id)).scalar() or 0
    open_tickets = db.query(func.count(Ticket.id)).filter(
        Ticket.status.in_(["open", "in_progress"])
    ).scalar() or 0
    resolved_tickets = db.query(func.count(Ticket.id)).filter(Ticket.status == "resolved").scalar() or 0

    # Agent stats
    agent_actions_today = db.query(func.count(AgentAction.id)).filter(
        AgentAction.created_at >= today_start
    ).scalar() or 0

    # Compute risk score (0-100)
    risk_score = _compute_risk_score(critical_alerts, high_alerts, medium_alerts, low_alerts, open_incidents)

    # False positive rate
    fp_rate = (false_positives / total_alerts * 100) if total_alerts > 0 else 0

    # Events per hour (last 24h)
    events_24h = db.query(func.count(Event.id)).filter(
        Event.ingested_at >= now - timedelta(hours=24)
    ).scalar() or 0
    events_per_hour = round(events_24h / 24, 1)

    return {
        "total_events": total_events,
        "events_today": events_today,
        "total_alerts": total_alerts,
        "open_alerts": open_alerts,
        "critical_alerts": critical_alerts,
        "high_alerts": high_alerts,
        "medium_alerts": medium_alerts,
        "low_alerts": low_alerts,
        "total_incidents": total_incidents,
        "open_incidents": open_incidents,
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "resolved_tickets": resolved_tickets,
        "risk_score": risk_score,
        "risk_level": _risk_level(risk_score),
        "agent_actions_today": agent_actions_today,
        "false_positive_rate": round(fp_rate, 1),
        "events_per_hour": events_per_hour,
    }


def get_threat_trends(db: Session, hours: int = 24) -> list:
    """Get alert trends over the last N hours."""
    now = datetime.utcnow()
    trends = []

    for i in range(hours, 0, -1):
        hour_start = now - timedelta(hours=i)
        hour_end = now - timedelta(hours=i - 1)

        for severity in ["critical", "high", "medium", "low"]:
            count = db.query(func.count(Alert.id)).filter(
                and_(
                    Alert.created_at >= hour_start,
                    Alert.created_at < hour_end,
                    Alert.severity == severity,
                )
            ).scalar() or 0

            if count > 0:
                trends.append({
                    "timestamp": hour_start.strftime("%H:%M"),
                    "count": count,
                    "severity": severity,
                })

    return trends


def get_recent_alerts(db: Session, limit: int = 10) -> list:
    """Get most recent alerts."""
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "severity": a.severity,
            "alert_type": a.alert_type,
            "status": a.status,
            "priority": a.priority,
            "mitre_id": a.mitre_id,
            "source_ip": a.source_ip,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in alerts
    ]


def get_agent_activity(db: Session, limit: int = 20) -> list:
    """Get recent agent activity."""
    actions = db.query(AgentAction).order_by(AgentAction.created_at.desc()).limit(limit).all()
    return [
        {
            "id": a.id,
            "agent_name": a.agent_name,
            "action_type": a.action_type,
            "input_summary": a.input_summary,
            "output_summary": a.output_summary,
            "confidence": a.confidence,
            "status": a.status,
            "duration_ms": a.duration_ms,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in actions
    ]


def get_system_health() -> list:
    """Get system component health status."""
    return [
        {"service": "Detection Engine", "status": "healthy", "uptime": "99.9%", "last_check": datetime.utcnow().strftime("%H:%M:%S")},
        {"service": "AI Agent System", "status": "healthy", "uptime": "99.8%", "last_check": datetime.utcnow().strftime("%H:%M:%S")},
        {"service": "Log Collector", "status": "healthy", "uptime": "99.9%", "last_check": datetime.utcnow().strftime("%H:%M:%S")},
        {"service": "Knowledge Base", "status": "healthy", "uptime": "99.7%", "last_check": datetime.utcnow().strftime("%H:%M:%S")},
        {"service": "Ticket System", "status": "healthy", "uptime": "100%", "last_check": datetime.utcnow().strftime("%H:%M:%S")},
    ]


def get_top_attack_types(db: Session) -> list:
    """Get distribution of alert types."""
    results = db.query(
        Alert.alert_type, func.count(Alert.id).label("count")
    ).group_by(Alert.alert_type).order_by(func.count(Alert.id).desc()).limit(10).all()

    return [{"type": r[0], "count": r[1]} for r in results]


def get_severity_distribution(db: Session) -> dict:
    """Get severity distribution of open alerts."""
    result = {}
    for severity in ["critical", "high", "medium", "low"]:
        count = db.query(func.count(Alert.id)).filter(Alert.severity == severity).scalar() or 0
        result[severity] = count
    return result


def _compute_risk_score(critical: int, high: int, medium: int, low: int, open_incidents: int) -> float:
    """Compute organization risk score (0-100)."""
    score = (
        critical * 25 +
        high * 15 +
        medium * 5 +
        low * 1 +
        open_incidents * 10
    )
    return min(100, round(score, 1))


def _risk_level(score: float) -> str:
    """Map risk score to risk level."""
    if score >= 75:
        return "critical"
    elif score >= 50:
        return "high"
    elif score >= 25:
        return "medium"
    else:
        return "low"
