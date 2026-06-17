"""
SecureFlow AI - Rule-Based Detection Engine
Implements signature-based threat detection rules with MITRE ATT&CK mapping.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models.event import Event
from app.models.alert import Alert
from app.config import settings


class DetectionRule:
    """Base class for detection rules."""

    def __init__(self):
        self.name = "base_rule"
        self.description = ""
        self.severity = "medium"
        self.mitre_id = ""
        self.mitre_tactic = ""
        self.mitre_technique_name = ""
        self.confidence = 0.8

    def evaluate(self, events: List[Dict], db: Session) -> List[Dict]:
        """Evaluate events against this rule. Returns list of alerts."""
        raise NotImplementedError


class SSHBruteForceRule(DetectionRule):
    """Detect SSH brute force attacks - T1110.001"""

    def __init__(self):
        super().__init__()
        self.name = "ssh_brute_force"
        self.description = "Multiple failed SSH login attempts from the same source IP"
        self.severity = "high"
        self.mitre_id = "T1110.001"
        self.mitre_tactic = "Credential Access"
        self.mitre_technique_name = "Brute Force: Password Guessing"
        self.confidence = 0.92
        self.threshold = settings.SSH_BRUTE_FORCE_THRESHOLD
        self.window_seconds = settings.SSH_BRUTE_FORCE_WINDOW_SECONDS

    def evaluate(self, events: List[Dict], db: Session) -> List[Dict]:
        alerts = []
        # Group SSH failures by source IP
        ssh_failures = defaultdict(list)
        for event in events:
            if (event.get("action") == "login_failed" and
                    event.get("source_name") in ["sshd", "auth.log", "ssh"]):
                ssh_failures[event.get("source_ip", "unknown")].append(event)

        for ip, failures in ssh_failures.items():
            if len(failures) >= self.threshold:
                # Check time window
                timestamps = [f.get("timestamp", datetime.utcnow()) for f in failures]
                if isinstance(timestamps[0], str):
                    timestamps = [datetime.fromisoformat(t) for t in timestamps]
                time_span = (max(timestamps) - min(timestamps)).total_seconds()

                if time_span <= self.window_seconds:
                    target_users = list(set(f.get("username", "unknown") for f in failures))
                    alerts.append({
                        "alert_type": self.name,
                        "severity": self.severity,
                        "confidence": self.confidence,
                        "title": f"SSH Brute Force Attack Detected from {ip}",
                        "description": (
                            f"Detected {len(failures)} failed SSH login attempts from IP {ip} "
                            f"within {int(time_span)} seconds. Target users: {', '.join(target_users)}. "
                            f"This pattern is consistent with automated password guessing attacks."
                        ),
                        "affected_assets": [ip] + target_users,
                        "evidence": {
                            "failed_attempts": len(failures),
                            "time_window_seconds": int(time_span),
                            "target_users": target_users,
                            "source_ip": ip,
                            "first_attempt": str(min(timestamps)),
                            "last_attempt": str(max(timestamps)),
                            "sample_logs": [f.get("raw_log", "")[:200] for f in failures[:3]],
                        },
                        "mitre_id": self.mitre_id,
                        "mitre_tactic": self.mitre_tactic,
                        "mitre_technique_name": self.mitre_technique_name,
                        "source_ip": ip,
                    })
        return alerts


class PortScanRule(DetectionRule):
    """Detect port scanning activity - T1046"""

    def __init__(self):
        super().__init__()
        self.name = "port_scan"
        self.description = "Connection attempts to multiple ports from a single source"
        self.severity = "medium"
        self.mitre_id = "T1046"
        self.mitre_tactic = "Discovery"
        self.mitre_technique_name = "Network Service Discovery"
        self.confidence = 0.85
        self.threshold = settings.PORT_SCAN_THRESHOLD
        self.window_seconds = settings.PORT_SCAN_WINDOW_SECONDS

    def evaluate(self, events: List[Dict], db: Session) -> List[Dict]:
        alerts = []
        port_attempts = defaultdict(set)
        ip_events = defaultdict(list)

        for event in events:
            if event.get("action") in ["port_scan", "connection_attempt", "syn_scan"]:
                ip = event.get("source_ip", "unknown")
                port = event.get("normalized_data", {}).get("dest_port", 0)
                port_attempts[ip].add(port)
                ip_events[ip].append(event)

        for ip, ports in port_attempts.items():
            if len(ports) >= self.threshold:
                alerts.append({
                    "alert_type": self.name,
                    "severity": self.severity,
                    "confidence": self.confidence,
                    "title": f"Port Scan Detected from {ip}",
                    "description": (
                        f"Source IP {ip} scanned {len(ports)} unique ports. "
                        f"Ports targeted: {', '.join(str(p) for p in sorted(list(ports))[:20])}. "
                        f"This is consistent with network reconnaissance activity."
                    ),
                    "affected_assets": [ip],
                    "evidence": {
                        "unique_ports": len(ports),
                        "ports_scanned": sorted(list(ports))[:50],
                        "source_ip": ip,
                        "total_attempts": len(ip_events[ip]),
                    },
                    "mitre_id": self.mitre_id,
                    "mitre_tactic": self.mitre_tactic,
                    "mitre_technique_name": self.mitre_technique_name,
                    "source_ip": ip,
                })
        return alerts


class FailedLoginBurstRule(DetectionRule):
    """Detect burst of failed login attempts across services - T1110"""

    def __init__(self):
        super().__init__()
        self.name = "failed_login_burst"
        self.description = "Burst of failed login attempts across multiple services"
        self.severity = "high"
        self.mitre_id = "T1110"
        self.mitre_tactic = "Credential Access"
        self.mitre_technique_name = "Brute Force"
        self.confidence = 0.88

    def evaluate(self, events: List[Dict], db: Session) -> List[Dict]:
        alerts = []
        failures_by_ip = defaultdict(list)

        for event in events:
            if event.get("action") == "login_failed":
                ip = event.get("source_ip", "unknown")
                failures_by_ip[ip].append(event)

        for ip, failures in failures_by_ip.items():
            if len(failures) >= settings.FAILED_LOGIN_THRESHOLD:
                services = list(set(f.get("source_name", "unknown") for f in failures))
                alerts.append({
                    "alert_type": self.name,
                    "severity": self.severity,
                    "confidence": self.confidence,
                    "title": f"Failed Login Burst from {ip}",
                    "description": (
                        f"Detected {len(failures)} failed login attempts from IP {ip} "
                        f"across services: {', '.join(services)}. "
                        f"This may indicate credential stuffing or brute force activity."
                    ),
                    "affected_assets": [ip] + services,
                    "evidence": {
                        "failed_count": len(failures),
                        "services_targeted": services,
                        "source_ip": ip,
                    },
                    "mitre_id": self.mitre_id,
                    "mitre_tactic": self.mitre_tactic,
                    "mitre_technique_name": self.mitre_technique_name,
                    "source_ip": ip,
                })
        return alerts


class SuspiciousPowerShellRule(DetectionRule):
    """Detect suspicious PowerShell usage - T1059.001"""

    def __init__(self):
        super().__init__()
        self.name = "suspicious_powershell"
        self.description = "Suspicious PowerShell command execution detected"
        self.severity = "critical"
        self.mitre_id = "T1059.001"
        self.mitre_tactic = "Execution"
        self.mitre_technique_name = "Command and Scripting Interpreter: PowerShell"
        self.confidence = 0.90

        self.suspicious_patterns = [
            "encodedcommand", "-enc", "-e ", "frombase64string",
            "downloadstring", "downloadfile", "invoke-webrequest",
            "invoke-expression", "iex", "new-object net.webclient",
            "-executionpolicy bypass", "hidden", "-windowstyle hidden",
            "invoke-mimikatz", "invoke-shellcode", "invoke-obfuscation",
        ]

    def evaluate(self, events: List[Dict], db: Session) -> List[Dict]:
        alerts = []
        for event in events:
            if event.get("source_name") in ["powershell", "windows_event", "sysmon"]:
                raw = event.get("raw_log", "").lower()
                matched = [p for p in self.suspicious_patterns if p in raw]
                if matched:
                    alerts.append({
                        "alert_type": self.name,
                        "severity": self.severity,
                        "confidence": self.confidence,
                        "title": f"Suspicious PowerShell Activity on {event.get('dest_ip', 'unknown host')}",
                        "description": (
                            f"Detected suspicious PowerShell command with indicators: "
                            f"{', '.join(matched)}. User: {event.get('username', 'unknown')}. "
                            f"This pattern is commonly associated with fileless malware and lateral movement."
                        ),
                        "affected_assets": [event.get("dest_ip", "unknown"), event.get("username", "unknown")],
                        "evidence": {
                            "matched_indicators": matched,
                            "username": event.get("username"),
                            "hostname": event.get("dest_ip"),
                            "raw_command_preview": raw[:300],
                        },
                        "mitre_id": self.mitre_id,
                        "mitre_tactic": self.mitre_tactic,
                        "mitre_technique_name": self.mitre_technique_name,
                        "source_ip": event.get("source_ip"),
                        "dest_ip": event.get("dest_ip"),
                    })
        return alerts


class PrivilegeEscalationRule(DetectionRule):
    """Detect privilege escalation attempts - T1548"""

    def __init__(self):
        super().__init__()
        self.name = "privilege_escalation"
        self.description = "Potential privilege escalation activity detected"
        self.severity = "critical"
        self.mitre_id = "T1548"
        self.mitre_tactic = "Privilege Escalation"
        self.mitre_technique_name = "Abuse Elevation Control Mechanism"
        self.confidence = 0.87

    def evaluate(self, events: List[Dict], db: Session) -> List[Dict]:
        alerts = []
        for event in events:
            if event.get("action") in ["privilege_escalation", "sudo_usage", "uac_bypass", "setuid"]:
                alerts.append({
                    "alert_type": self.name,
                    "severity": self.severity,
                    "confidence": self.confidence,
                    "title": f"Privilege Escalation Detected - {event.get('username', 'unknown')}",
                    "description": (
                        f"Privilege escalation activity detected for user '{event.get('username', 'unknown')}' "
                        f"on {event.get('dest_ip', 'unknown host')}. "
                        f"Action: {event.get('action')}. This may indicate an attacker attempting "
                        f"to gain elevated access after initial compromise."
                    ),
                    "affected_assets": [
                        event.get("dest_ip", "unknown"),
                        event.get("username", "unknown"),
                    ],
                    "evidence": {
                        "action": event.get("action"),
                        "username": event.get("username"),
                        "hostname": event.get("dest_ip"),
                        "raw_log": event.get("raw_log", "")[:300],
                    },
                    "mitre_id": self.mitre_id,
                    "mitre_tactic": self.mitre_tactic,
                    "mitre_technique_name": self.mitre_technique_name,
                    "source_ip": event.get("source_ip"),
                })
        return alerts


class MalwareActivityRule(DetectionRule):
    """Detect malware-like activity - T1204"""

    def __init__(self):
        super().__init__()
        self.name = "malware_activity"
        self.description = "Suspicious activity consistent with malware execution"
        self.severity = "critical"
        self.mitre_id = "T1204"
        self.mitre_tactic = "Execution"
        self.mitre_technique_name = "User Execution"
        self.confidence = 0.85

    def evaluate(self, events: List[Dict], db: Session) -> List[Dict]:
        alerts = []
        for event in events:
            if event.get("action") in ["malware_detected", "suspicious_process", "c2_communication"]:
                alerts.append({
                    "alert_type": self.name,
                    "severity": self.severity,
                    "confidence": self.confidence,
                    "title": f"Malware Activity Detected on {event.get('dest_ip', 'unknown')}",
                    "description": (
                        f"Suspicious activity consistent with malware execution detected on "
                        f"{event.get('dest_ip', 'unknown host')}. "
                        f"Action type: {event.get('action')}. "
                        f"Immediate investigation recommended."
                    ),
                    "affected_assets": [event.get("dest_ip", "unknown")],
                    "evidence": {
                        "action": event.get("action"),
                        "hostname": event.get("dest_ip"),
                        "raw_log": event.get("raw_log", "")[:300],
                        "process_info": event.get("normalized_data", {}),
                    },
                    "mitre_id": self.mitre_id,
                    "mitre_tactic": self.mitre_tactic,
                    "mitre_technique_name": self.mitre_technique_name,
                    "source_ip": event.get("source_ip"),
                })
        return alerts


# Registry of all detection rules
ALL_RULES = [
    SSHBruteForceRule(),
    PortScanRule(),
    FailedLoginBurstRule(),
    SuspiciousPowerShellRule(),
    PrivilegeEscalationRule(),
    MalwareActivityRule(),
]


def run_all_rules(events: List[Dict], db: Session) -> List[Dict]:
    """Run all detection rules against a set of events."""
    all_alerts = []
    for rule in ALL_RULES:
        try:
            alerts = rule.evaluate(events, db)
            all_alerts.extend(alerts)
        except Exception as e:
            print(f"Error running rule {rule.name}: {e}")
    return all_alerts
