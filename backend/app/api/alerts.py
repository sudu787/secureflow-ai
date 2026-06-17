"""Alerts API - Security alert management with AI analysis."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.alert import Alert
from app.schemas.alerts import AlertResponse, AlertUpdate
from app.agents.orchestrator import Orchestrator

router = APIRouter()


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    return query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(alert_id: int, data: AlertUpdate, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(alert, key, value)

    db.commit()
    db.refresh(alert)
    return alert


@router.post("/{alert_id}/analyze")
async def analyze_alert(alert_id: int, db: Session = Depends(get_db)):
    """Run full AI analysis on an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert_dict = {
        "id": alert.id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "confidence": alert.confidence,
        "title": alert.title,
        "description": alert.description,
        "affected_assets": alert.affected_assets,
        "evidence": alert.evidence or {},
        "mitre_id": alert.mitre_id,
        "mitre_tactic": alert.mitre_tactic,
        "mitre_technique_name": alert.mitre_technique_name,
        "source_ip": alert.source_ip,
        "dest_ip": alert.dest_ip,
    }

    orchestrator = Orchestrator()
    result = orchestrator.analyze_alert(alert_dict, db)

    # Update alert with investigation results
    alert.status = "investigating"
    alert.priority = result.get("triage", {}).get("priority", alert.priority)
    alert.investigation_summary = result.get("investigation", {}).get("detailed_summary", "")
    alert.remediation_plan = result.get("remediation", {}).get("remediation_summary", "")
    db.commit()

    return result
