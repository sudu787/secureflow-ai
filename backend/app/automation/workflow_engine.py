"""
SecureFlow AI — Workflow Automation Engine
Predefined automation workflows for threat response and IT support.
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.automation.notification_service import create_notification

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Executes predefined automation workflows."""

    def __init__(self):
        from app.agents.orchestrator import Orchestrator
        self.orchestrator = Orchestrator()

    def run_threat_response(self, alert_data: Dict, db: Session) -> Dict[str, Any]:
        """
        Full threat response workflow:
        Detect → Triage → Investigate → Remediate → Report → Ticket → Notify
        """
        logger.info(f"🔄 Starting threat response workflow for: {alert_data.get('title', 'Unknown')}")

        # Run full AI analysis pipeline (triage → investigate → remediate → report)
        analysis = self.orchestrator.analyze_alert(alert_data, db)

        # Create notification for P1/P2 alerts
        priority = analysis.get("triage", {}).get("priority", "P3")
        if priority in ("P1", "P2"):
            create_notification(
                db=db,
                title=f"🚨 {priority} Alert: {alert_data.get('title', 'Security Alert')}",
                message=(
                    f"A {priority} security alert has been triaged by AI. "
                    f"Severity: {alert_data.get('severity', 'unknown')}. "
                    f"Confidence: {analysis.get('confidence', 0):.0%}. "
                    f"Incident #{analysis.get('incident_id', 'N/A')} created."
                ),
                severity="critical" if priority == "P1" else "warning",
                category="alert",
                related_alert_id=alert_data.get("id"),
                related_incident_id=analysis.get("incident_id"),
            )

        logger.info(
            f"✅ Threat response complete — "
            f"Priority: {priority}, Incident: #{analysis.get('incident_id', 'N/A')}, "
            f"Ticket: #{analysis.get('ticket_created', 'N/A')}"
        )

        return {
            "workflow": "threat_response",
            "status": "completed",
            "analysis": analysis,
        }

    def run_it_support(self, message: str, db: Session) -> Dict[str, Any]:
        """
        IT support workflow:
        Classify → Diagnose → Suggest Fix → Create Ticket → Escalate if needed
        """
        result = self.orchestrator.handle_chat_message(message, session_type="it_support", db=db)

        if result.get("ticket_created"):
            create_notification(
                db=db,
                title="🎫 IT Support Ticket Created",
                message=f"A new IT support ticket #{result['ticket_created']} was created by AI.",
                severity="info",
                category="ticket",
            )

        return {
            "workflow": "it_support",
            "status": "completed",
            "result": result,
        }
