"""Alert model for detected security threats."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, func
from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    alert_type = Column(String(100), nullable=False, index=True)  # brute_force, port_scan, malware, etc.
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    confidence = Column(Float, default=0.0)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    affected_assets = Column(JSON, nullable=True)  # list of IPs, hostnames, users
    evidence = Column(JSON, nullable=True)  # supporting evidence data
    mitre_id = Column(String(20), nullable=True)  # MITRE ATT&CK technique ID
    mitre_tactic = Column(String(100), nullable=True)  # MITRE tactic name
    mitre_technique_name = Column(String(200), nullable=True)
    source_ip = Column(String(50), nullable=True)
    dest_ip = Column(String(50), nullable=True)
    status = Column(String(30), default="open", index=True)  # open, investigating, resolved, false_positive
    priority = Column(String(5), default="P3")  # P1, P2, P3, P4
    assigned_to = Column(String(100), nullable=True)
    investigation_summary = Column(Text, nullable=True)
    remediation_plan = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime, nullable=True)
