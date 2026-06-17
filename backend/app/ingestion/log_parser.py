"""
SecureFlow AI — Log Parser
Regex-based parsers for multiple log formats.
Auto-detects log format and extracts structured fields.
"""

import re
import json
from datetime import datetime
from typing import Dict, Optional, List


class LogParser:
    """Multi-format log parser with auto-detection."""

    # ── Format-specific parsers ──────────────────────────────────────

    _AUTH_LOG_PATTERN = re.compile(
        r"(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
        r"(?P<host>\S+)\s+"
        r"(?P<service>\S+?)(\[(?P<pid>\d+)\])?\s*:\s*"
        r"(?P<message>.*)"
    )

    _NGINX_PATTERN = re.compile(
        r"(?P<source_ip>\d+\.\d+\.\d+\.\d+)\s+-\s+(?P<user>\S+)\s+"
        r"\[(?P<timestamp>[^\]]+)\]\s+"
        r'"(?P<method>\w+)\s+(?P<path>\S+)\s+\S+"\s+'
        r"(?P<status>\d+)\s+(?P<bytes>\d+)"
    )

    _SYSLOG_PATTERN = re.compile(
        r"(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
        r"(?P<host>\S+)\s+"
        r"(?P<process>\S+?)(\[(?P<pid>\d+)\])?\s*:\s*"
        r"(?P<message>.*)"
    )

    _SURICATA_EVE_KEYS = {"timestamp", "event_type", "src_ip", "dest_ip"}

    @classmethod
    def parse(cls, raw_log: str, source_hint: str = None) -> Optional[Dict]:
        """
        Parse a raw log line into a normalized event dict.

        Returns None if the log cannot be parsed.
        """
        if not raw_log or not raw_log.strip():
            return None

        raw_log = raw_log.strip()

        # Try JSON first (Suricata EVE, Windows JSON events)
        if raw_log.startswith("{"):
            return cls._parse_json_log(raw_log)

        # Try format-specific parsers
        if source_hint == "auth.log" or "sshd[" in raw_log or "sudo:" in raw_log:
            return cls._parse_auth_log(raw_log)

        if source_hint == "nginx" or ('" ' in raw_log and re.search(r"\d+\.\d+\.\d+\.\d+ -", raw_log)):
            return cls._parse_nginx_log(raw_log)

        # Generic syslog
        result = cls._parse_syslog(raw_log)
        if result:
            return result

        # Fallback — store as unparsed event
        return {
            "source_type": "unknown",
            "source_name": source_hint or "raw",
            "raw_log": raw_log,
            "action": "unparsed",
            "severity": "info",
            "confidence": 0.3,
            "timestamp": datetime.utcnow(),
        }

    @classmethod
    def _parse_auth_log(cls, raw_log: str) -> Optional[Dict]:
        match = cls._AUTH_LOG_PATTERN.match(raw_log)
        if not match:
            return None

        d = match.groupdict()
        message = d.get("message", "")
        service = d.get("service", "")

        event = {
            "source_type": "linux",
            "source_name": "sshd" if "sshd" in service else "auth.log",
            "raw_log": raw_log,
            "timestamp": cls._parse_syslog_timestamp(d.get("timestamp", "")),
            "normalized_data": {"pid": d.get("pid"), "service": service},
        }

        # Extract action and details from message
        if "Failed password" in message:
            ip_match = re.search(r"from\s+(\d+\.\d+\.\d+\.\d+)", message)
            user_match = re.search(r"for\s+(?:invalid\s+user\s+)?(\S+)", message)
            event.update({
                "action": "login_failed",
                "source_ip": ip_match.group(1) if ip_match else None,
                "username": user_match.group(1) if user_match else None,
                "dest_ip": d.get("host"),
                "severity": "medium",
                "confidence": 0.9,
                "mitre_technique": "T1110.001",
                "mitre_tactic": "Credential Access",
            })
        elif "Accepted" in message:
            ip_match = re.search(r"from\s+(\d+\.\d+\.\d+\.\d+)", message)
            user_match = re.search(r"for\s+(\S+)", message)
            event.update({
                "action": "login_success",
                "source_ip": ip_match.group(1) if ip_match else None,
                "username": user_match.group(1) if user_match else None,
                "dest_ip": d.get("host"),
                "severity": "info",
                "confidence": 0.95,
            })
        elif "sudo:" in raw_log and "COMMAND=" in message:
            user_match = re.search(r"^\s*(\S+)\s*:", message)
            cmd_match = re.search(r"COMMAND=(.+)", message)
            event.update({
                "action": "privilege_escalation",
                "username": user_match.group(1) if user_match else None,
                "dest_ip": d.get("host"),
                "severity": "high",
                "confidence": 0.87,
                "mitre_technique": "T1548",
                "mitre_tactic": "Privilege Escalation",
                "normalized_data": {
                    **event.get("normalized_data", {}),
                    "command": cmd_match.group(1) if cmd_match else None,
                },
            })
        else:
            event.update({
                "action": "auth_event",
                "severity": "info",
                "confidence": 0.7,
            })

        return event

    @classmethod
    def _parse_nginx_log(cls, raw_log: str) -> Optional[Dict]:
        match = cls._NGINX_PATTERN.match(raw_log)
        if not match:
            return None

        d = match.groupdict()
        status = int(d.get("status", 200))
        severity = "info"
        action = "web_request"

        if status >= 500:
            severity = "high"
            action = "server_error"
        elif status == 403:
            severity = "medium"
            action = "access_denied"
        elif status == 404 and any(p in d.get("path", "") for p in [".php", "admin", "wp-", ".env", "/.git"]):
            severity = "medium"
            action = "web_scan"

        return {
            "source_type": "web",
            "source_name": "nginx",
            "raw_log": raw_log,
            "source_ip": d.get("source_ip"),
            "username": d.get("user") if d.get("user") != "-" else None,
            "action": action,
            "severity": severity,
            "confidence": 0.85,
            "timestamp": cls._parse_nginx_timestamp(d.get("timestamp", "")),
            "normalized_data": {
                "method": d.get("method"),
                "path": d.get("path"),
                "status": status,
                "bytes": int(d.get("bytes", 0)),
            },
        }

    @classmethod
    def _parse_json_log(cls, raw_log: str) -> Optional[Dict]:
        try:
            data = json.loads(raw_log)
        except json.JSONDecodeError:
            return None

        # Suricata EVE format
        if "event_type" in data:
            event_type = data.get("event_type", "")
            severity = "info"
            action = event_type

            if event_type == "alert":
                severity = data.get("alert", {}).get("severity", 1)
                severity = {1: "critical", 2: "high", 3: "medium"}.get(severity, "medium")
                action = data.get("alert", {}).get("action", "alert")

            return {
                "source_type": "network",
                "source_name": "suricata",
                "raw_log": raw_log,
                "source_ip": data.get("src_ip"),
                "dest_ip": data.get("dest_ip"),
                "action": action,
                "severity": severity,
                "confidence": 0.88,
                "timestamp": cls._parse_iso_timestamp(data.get("timestamp", "")),
                "normalized_data": {
                    "src_port": data.get("src_port"),
                    "dest_port": data.get("dest_port"),
                    "protocol": data.get("proto"),
                    "alert_signature": data.get("alert", {}).get("signature", ""),
                },
            }

        # Windows Event JSON
        if "EventID" in data or "event_id" in data:
            return {
                "source_type": "windows",
                "source_name": "windows_event",
                "raw_log": raw_log,
                "action": f"event_{data.get('EventID', data.get('event_id', 'unknown'))}",
                "severity": "info",
                "confidence": 0.8,
                "timestamp": cls._parse_iso_timestamp(data.get("TimeCreated", data.get("timestamp", ""))),
                "username": data.get("TargetUserName", data.get("username")),
                "source_ip": data.get("IpAddress", data.get("source_ip")),
                "normalized_data": data,
            }

        return None

    @classmethod
    def _parse_syslog(cls, raw_log: str) -> Optional[Dict]:
        match = cls._SYSLOG_PATTERN.match(raw_log)
        if not match:
            return None

        d = match.groupdict()
        return {
            "source_type": "linux",
            "source_name": d.get("process", "syslog"),
            "raw_log": raw_log,
            "action": "syslog_event",
            "severity": "info",
            "confidence": 0.7,
            "timestamp": cls._parse_syslog_timestamp(d.get("timestamp", "")),
            "normalized_data": {
                "process": d.get("process"),
                "pid": d.get("pid"),
                "message": d.get("message"),
            },
        }

    # ── Timestamp helpers ────────────────────────────────────────────

    @staticmethod
    def _parse_syslog_timestamp(ts: str) -> datetime:
        try:
            return datetime.strptime(f"{datetime.utcnow().year} {ts}", "%Y %b %d %H:%M:%S")
        except (ValueError, TypeError):
            return datetime.utcnow()

    @staticmethod
    def _parse_nginx_timestamp(ts: str) -> datetime:
        try:
            return datetime.strptime(ts, "%d/%b/%Y:%H:%M:%S %z").replace(tzinfo=None)
        except (ValueError, TypeError):
            return datetime.utcnow()

    @staticmethod
    def _parse_iso_timestamp(ts: str) -> datetime:
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
        except (ValueError, TypeError, AttributeError):
            return datetime.utcnow()
