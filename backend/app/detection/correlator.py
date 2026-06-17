"""
SecureFlow AI - Event Correlation Engine
Correlates alerts across multiple detection sources to identify attack chains
and reduce false positives through multi-signal validation.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict


# Known attack chains - sequences of MITRE techniques that form kill chains
ATTACK_CHAINS = {
    "full_intrusion": {
        "name": "Full Network Intrusion",
        "techniques": ["T1046", "T1110", "T1078", "T1548"],
        "min_match": 3,
        "severity": "critical",
        "description": "Reconnaissance → Brute Force → Valid Account Use → Privilege Escalation",
    },
    "malware_chain": {
        "name": "Malware Execution Chain",
        "techniques": ["T1566", "T1204", "T1059.001", "T1548"],
        "min_match": 2,
        "severity": "critical",
        "description": "Phishing → User Execution → PowerShell → Privilege Escalation",
    },
    "credential_theft": {
        "name": "Credential Theft Campaign",
        "techniques": ["T1110", "T1110.001", "T1078"],
        "min_match": 2,
        "severity": "high",
        "description": "Brute Force → Password Guessing → Valid Account Access",
    },
    "recon_attack": {
        "name": "Reconnaissance to Attack",
        "techniques": ["T1046", "T1110"],
        "min_match": 2,
        "severity": "high",
        "description": "Port Scan → Brute Force Attack",
    },
}


def correlate_alerts(alerts: List[Dict], time_window_minutes: int = 30) -> List[Dict]:
    """
    Correlate alerts to detect attack chains and multi-stage attacks.

    Args:
        alerts: List of alert dicts with mitre_id, source_ip, timestamp
        time_window_minutes: Time window for correlation

    Returns:
        List of correlated incident dicts
    """
    incidents = []

    # Group alerts by source IP
    alerts_by_ip = defaultdict(list)
    for alert in alerts:
        ip = alert.get("source_ip", "unknown")
        alerts_by_ip[ip].append(alert)

    # Check each IP's alerts against known attack chains
    for ip, ip_alerts in alerts_by_ip.items():
        if len(ip_alerts) < 2:
            continue

        techniques_seen = set()
        for alert in ip_alerts:
            mitre_id = alert.get("mitre_id", "")
            if mitre_id:
                techniques_seen.add(mitre_id)

        # Check against known chains
        for chain_id, chain in ATTACK_CHAINS.items():
            matched = techniques_seen.intersection(set(chain["techniques"]))
            if len(matched) >= chain["min_match"]:
                related_alerts = [
                    a for a in ip_alerts
                    if a.get("mitre_id") in matched
                ]
                incidents.append({
                    "type": "correlated_incident",
                    "chain_id": chain_id,
                    "chain_name": chain["name"],
                    "severity": chain["severity"],
                    "description": (
                        f"Attack chain detected from IP {ip}: {chain['description']}. "
                        f"Matched {len(matched)}/{len(chain['techniques'])} techniques: "
                        f"{', '.join(matched)}."
                    ),
                    "source_ip": ip,
                    "techniques_matched": list(matched),
                    "related_alerts": related_alerts,
                    "confidence": min(0.95, 0.6 + len(matched) * 0.1),
                    "attack_path": chain["description"],
                })

    return incidents
