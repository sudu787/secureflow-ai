"""Event model for normalized log/telemetry events."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, func
from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(50), nullable=False, index=True)  # linux, windows, web, network, cloud
    source_name = Column(String(100), nullable=False)  # auth.log, syslog, apache, suricata, etc.
    raw_log = Column(Text, nullable=False)
    normalized_data = Column(JSON, nullable=True)
    severity = Column(String(20), default="info", index=True)  # info, low, medium, high, critical
    confidence = Column(Float, default=0.0)
    mitre_technique = Column(String(20), nullable=True)  # e.g., T1110.001
    mitre_tactic = Column(String(50), nullable=True)  # e.g., Credential Access
    source_ip = Column(String(50), nullable=True, index=True)
    dest_ip = Column(String(50), nullable=True)
    username = Column(String(100), nullable=True, index=True)
    action = Column(String(100), nullable=True)  # login_failed, port_scan, process_exec, etc.
    timestamp = Column(DateTime, nullable=False, index=True)
    ingested_at = Column(DateTime, server_default=func.now())
