"""
SecureFlow AI - Audit Logger
Records all security-relevant actions for compliance and forensics.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    severity: str = "info",
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
):
    """Log a security-relevant action."""
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        severity=severity,
        ip_address=ip_address,
        created_at=datetime.utcnow(),
    )
    db.add(log_entry)
    db.commit()
    return log_entry


def log_prompt_injection(
    db: Session,
    findings: list,
    original_input: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
):
    """Log a detected prompt injection attempt."""
    return log_action(
        db=db,
        action="prompt_injection_blocked",
        resource_type="chat",
        details={
            "findings": findings,
            "input_preview": original_input[:200],  # Truncate for safety
            "timestamp": datetime.utcnow().isoformat(),
        },
        severity="critical",
        user_id=user_id,
        ip_address=ip_address,
    )


def log_policy_violation(
    db: Session,
    violations: list,
    context: str = "",
    user_id: Optional[int] = None,
):
    """Log a policy violation in AI output."""
    return log_action(
        db=db,
        action="policy_violation",
        resource_type="ai_output",
        details={
            "violations": violations,
            "context": context[:200],
            "timestamp": datetime.utcnow().isoformat(),
        },
        severity="warning",
        user_id=user_id,
    )
