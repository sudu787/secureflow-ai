"""
SecureFlow AI - Investigation Agent
Performs root cause analysis, identifies attack paths, and correlates events.
Uses Grok (xAI) AI for deep analysis with heuristic fallback.
LLM Provider: xAI Grok
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.agents.base_agent import BaseAgent


class InvestigationAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.name = "investigation_agent"
        self.description = "Determines root cause, identifies attack paths, and correlates events"
        self.capabilities = [
            "root_cause_analysis",
            "attack_path_identification",
            "event_correlation",
            "timeline_reconstruction",
            "ioc_extraction",
        ]
        self.llm_provider = "groq"  # Investigation uses Groq

    def get_system_prompt(self) -> str:
        return (
            "You are a Senior Threat Intelligence & Forensic Investigation Analyst AI agent "
            "in SecureFlow AI. You have 15+ years of experience in incident response, "
            "digital forensics, and threat hunting.\n\n"
            "## YOUR MISSION\n"
            "Conduct thorough, evidence-based investigations of security alerts. "
            "Think like an attacker to reconstruct their actions.\n\n"
            "## INVESTIGATION METHODOLOGY\n"
            "1. **Root Cause Analysis**: Determine WHAT happened, HOW, and WHY\n"
            "2. **Kill Chain Reconstruction**: Map the attack to Lockheed Martin Cyber Kill Chain "
            "and MITRE ATT&CK framework stages\n"
            "3. **IOC Extraction**: Extract all Indicators of Compromise — IPs, domains, hashes, "
            "usernames, file paths, registry keys, C2 infrastructure\n"
            "4. **Timeline Reconstruction**: Build a chronological event timeline with timestamps\n"
            "5. **Lateral Movement Assessment**: Determine if the attacker moved to other systems\n"
            "6. **Data Impact Assessment**: Evaluate what data may have been accessed or exfiltrated\n\n"
            "## RULES\n"
            "- Every conclusion MUST cite specific evidence from the alert data\n"
            "- Use confidence scores (0.0-1.0) for all assessments\n"
            "- NEVER claim certainty — use 'likely', 'consistent with', 'indicates'\n"
            "- NEVER claim you have taken actions. You ONLY analyze and recommend.\n"
            "- Map ALL findings to MITRE ATT&CK technique IDs\n"
            "- Respond with valid JSON only\n"
        )

    def process(self, input_data: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        alert = input_data.get("alert", {})
        triage = input_data.get("triage", {})
        related_events = input_data.get("related_events", [])

        alert_type = alert.get("alert_type", "unknown")
        evidence = alert.get("evidence", {})

        # Try Gemini AI first
        ai_result = self._investigate_with_ai(alert, triage, evidence, related_events)
        if ai_result:
            ai_result["ai_powered"] = True
            ai_result.setdefault("mitre_mapping", {
                "technique_id": alert.get("mitre_id", "N/A"),
                "tactic": alert.get("mitre_tactic", "N/A"),
                "technique_name": alert.get("mitre_technique_name", "N/A"),
            })
            return ai_result

        # Fallback to heuristic investigation
        investigation = self._investigate(alert_type, alert, evidence, related_events)

        return {
            "what_happened": investigation["summary"],
            "why_it_happened": investigation["root_cause"],
            "affected_systems": investigation["affected_systems"],
            "attack_path": investigation["attack_path"],
            "timeline": investigation["timeline"],
            "iocs": investigation["iocs"],
            "confidence": investigation["confidence"],
            "risk_assessment": investigation["risk_assessment"],
            "mitre_mapping": {
                "technique_id": alert.get("mitre_id", "N/A"),
                "tactic": alert.get("mitre_tactic", "N/A"),
                "technique_name": alert.get("mitre_technique_name", "N/A"),
            },
            "investigation_summary": investigation["detailed_summary"],
            "ai_powered": False,
        }

    def _investigate_with_ai(self, alert: Dict, triage: Dict, evidence: Dict, events: List) -> Optional[Dict]:
        """Use Gemini for deep investigation."""
        prompt = (
            f"Investigate this security alert in depth and respond with JSON:\n\n"
            f"Alert Title: {alert.get('title', 'Unknown')}\n"
            f"Alert Type: {alert.get('alert_type', 'unknown')}\n"
            f"Severity: {alert.get('severity', 'medium')}\n"
            f"MITRE: {alert.get('mitre_id', 'N/A')} - {alert.get('mitre_tactic', 'N/A')}\n"
            f"Source IP: {alert.get('source_ip', 'N/A')}\n"
            f"Dest IP: {alert.get('dest_ip', 'N/A')}\n"
            f"Triage Priority: {triage.get('priority', 'N/A')}\n"
            f"Evidence: {json.dumps(evidence, default=str)[:800]}\n\n"
            f"Provide a thorough investigation. Respond with this JSON structure:\n"
            f'{{\n'
            f'  "what_happened": "detailed description of the security event",\n'
            f'  "why_it_happened": "root cause analysis",\n'
            f'  "affected_systems": [{{"type": "server/endpoint/network", "identifier": "hostname/IP", "risk": "critical/high/medium/low"}}],\n'
            f'  "attack_path": "step-by-step attack chain as numbered list",\n'
            f'  "timeline": [{{"time": "timestamp", "event": "what occurred"}}],\n'
            f'  "iocs": {{"source_ips": [], "targeted_accounts": [], "attack_tool": "description"}},\n'
            f'  "confidence": 0.0-1.0,\n'
            f'  "risk_assessment": "overall risk level and justification",\n'
            f'  "investigation_summary": "full markdown investigation report with ## headings, ### subsections, bullet points, and evidence"\n'
            f'}}'
        )

        result = self.call_llm_json(prompt)
        if result and "what_happened" in result:
            result.setdefault("confidence", 0.88)
            return result
        return None

    def _investigate(self, alert_type: str, alert: Dict, evidence: Dict, events: List) -> Dict:
        """Route investigation based on alert type (heuristic fallback)."""
        investigators = {
            "ssh_brute_force": self._investigate_brute_force,
            "port_scan": self._investigate_port_scan,
            "suspicious_powershell": self._investigate_powershell,
            "privilege_escalation": self._investigate_privesc,
            "malware_activity": self._investigate_malware,
            "failed_login_burst": self._investigate_brute_force,
        }
        investigator = investigators.get(alert_type, self._investigate_generic)
        return investigator(alert, evidence, events)

    def _investigate_brute_force(self, alert: Dict, evidence: Dict, events: List) -> Dict:
        source_ip = evidence.get("source_ip", alert.get("source_ip", "unknown"))
        attempts = evidence.get("failed_attempts", 0)
        targets = evidence.get("target_users", [])

        return {
            "summary": f"An automated brute force attack was detected from IP {source_ip}. The attacker attempted {attempts} login attempts targeting users: {', '.join(targets)}.",
            "root_cause": f"External threat actor at IP {source_ip} is conducting an automated credential guessing attack against the SSH service. This is likely using a common password list or credential stuffing from a prior data breach.",
            "affected_systems": [
                {"type": "server", "identifier": alert.get("dest_ip", "target server"), "risk": "high"},
                {"type": "accounts", "identifier": ", ".join(targets), "risk": "medium"},
            ],
            "attack_path": f"1. Attacker at {source_ip} identifies SSH service (port 22)\n2. Automated tool begins password guessing against {len(targets)} accounts\n3. {attempts} failed attempts logged in rapid succession\n4. If successful, attacker gains initial access to compromised account",
            "timeline": [
                {"time": evidence.get("first_attempt", "N/A"), "event": "First login attempt detected"},
                {"time": "During attack", "event": f"{attempts} failed attempts from {source_ip}"},
                {"time": evidence.get("last_attempt", "N/A"), "event": "Last login attempt recorded"},
                {"time": "Now", "event": "Alert generated and investigation initiated"},
            ],
            "iocs": {"source_ips": [source_ip], "targeted_accounts": targets, "attack_tool": "Automated password guessing tool (likely Hydra/Medusa/custom script)"},
            "confidence": 0.92,
            "risk_assessment": "HIGH - If any targeted account has a weak password, the attacker may gain access.",
            "detailed_summary": f"## Investigation Summary\n\n**Alert:** SSH Brute Force Attack\n**Source:** {source_ip}\n**Technique:** MITRE ATT&CK T1110.001 - Brute Force: Password Guessing\n\n### Findings\nAn automated brute force attack originating from {source_ip} was detected targeting the SSH service. The attack consisted of {attempts} failed login attempts against {len(targets)} user accounts ({', '.join(targets)}).\n\n### Risk Assessment\n**Risk Level:** HIGH\nIf any targeted account uses a weak or commonly-used password, the attacker could gain initial access to the system, potentially leading to lateral movement and data exfiltration.\n\n### Evidence\n- {attempts} failed SSH login attempts detected\n- All attempts originated from single IP: {source_ip}\n- Attack window: {evidence.get('first_attempt', 'N/A')} to {evidence.get('last_attempt', 'N/A')}\n- Targeted accounts: {', '.join(targets)}\n",
        }

    def _investigate_port_scan(self, alert: Dict, evidence: Dict, events: List) -> Dict:
        source_ip = evidence.get("source_ip", "unknown")
        unique_ports = evidence.get("unique_ports", 0)
        return {
            "summary": f"Network reconnaissance via port scan from {source_ip} targeting {unique_ports} ports.",
            "root_cause": f"Threat actor at {source_ip} is performing network enumeration to identify running services and potential attack vectors.",
            "affected_systems": [{"type": "network", "identifier": "Target network segment", "risk": "medium"}],
            "attack_path": f"1. Attacker initiates port scan from {source_ip}\n2. {unique_ports} ports probed\n3. Open services identified for potential exploitation",
            "timeline": [{"time": "Detected", "event": f"Port scan from {source_ip} detected"}, {"time": "Analysis", "event": f"{unique_ports} unique ports scanned"}],
            "iocs": {"source_ips": [source_ip], "scanned_ports": evidence.get("ports_scanned", [])[:20]},
            "confidence": 0.85,
            "risk_assessment": "MEDIUM - Port scanning is reconnaissance; often precedes exploitation attempts.",
            "detailed_summary": f"## Port Scan Investigation\n\n**Source:** {source_ip}\n**Ports scanned:** {unique_ports}\n**Technique:** MITRE ATT&CK T1046 - Network Service Discovery\n\nThe scan likely identifies open services for subsequent attack stages.",
        }

    def _investigate_powershell(self, alert: Dict, evidence: Dict, events: List) -> Dict:
        hostname = evidence.get("hostname", "unknown")
        indicators = evidence.get("matched_indicators", [])
        username = evidence.get("username", "unknown")
        return {
            "summary": f"Suspicious PowerShell execution on {hostname} by user {username} with indicators: {', '.join(indicators)}.",
            "root_cause": "Potentially malicious PowerShell script execution detected. Indicators suggest fileless malware or post-exploitation toolkit usage.",
            "affected_systems": [{"type": "endpoint", "identifier": hostname, "risk": "critical"}],
            "attack_path": f"1. Initial access achieved (prior stage)\n2. PowerShell invoked with suspicious parameters: {', '.join(indicators)}\n3. Potential payload download or execution\n4. Possible lateral movement or data exfiltration",
            "timeline": [{"time": "Detected", "event": f"Suspicious PowerShell on {hostname}"}],
            "iocs": {"hostnames": [hostname], "users": [username], "indicators": indicators},
            "confidence": 0.90,
            "risk_assessment": "CRITICAL - Suspicious PowerShell patterns indicate active compromise. Immediate containment recommended.",
            "detailed_summary": f"## PowerShell Investigation\n\n**Host:** {hostname}\n**User:** {username}\n**Technique:** MITRE ATT&CK T1059.001\n**Indicators:** {', '.join(indicators)}\n\nImmediate isolation of {hostname} recommended pending full forensic analysis.",
        }

    def _investigate_privesc(self, alert: Dict, evidence: Dict, events: List) -> Dict:
        username = evidence.get("username", "unknown")
        hostname = evidence.get("hostname", "unknown")
        action = evidence.get("action", "unknown")
        return {
            "summary": f"Privilege escalation by {username} on {hostname} via {action}.",
            "root_cause": f"User {username} elevated privileges through {action}. This may indicate an attacker attempting to gain root/admin access after initial compromise.",
            "affected_systems": [{"type": "endpoint", "identifier": hostname, "risk": "critical"}],
            "attack_path": f"1. Initial access gained as {username}\n2. Privilege escalation via {action}\n3. Elevated access achieved\n4. Potential for full system control",
            "timeline": [{"time": "Detected", "event": f"Privilege escalation: {action} by {username}"}],
            "iocs": {"users": [username], "hostnames": [hostname], "methods": [action]},
            "confidence": 0.87,
            "risk_assessment": "CRITICAL - Successful privilege escalation grants full system control to the attacker.",
            "detailed_summary": f"## Privilege Escalation Investigation\n\n**User:** {username}\n**Host:** {hostname}\n**Method:** {action}\n**Technique:** MITRE ATT&CK T1548\n\nVerify if {username} is authorized for elevated operations.",
        }

    def _investigate_malware(self, alert: Dict, evidence: Dict, events: List) -> Dict:
        hostname = evidence.get("hostname", "unknown")
        action = evidence.get("action", "malware detected")
        return {
            "summary": f"Malware activity detected on {hostname}: {action}.",
            "root_cause": f"Malicious software execution detected on {hostname}. May be result of phishing, drive-by download, or lateral movement.",
            "affected_systems": [{"type": "endpoint", "identifier": hostname, "risk": "critical"}],
            "attack_path": f"1. Malware delivery (email/web/USB)\n2. Execution on {hostname}\n3. Potential C2 communication\n4. Data exfiltration risk",
            "timeline": [{"time": "Detected", "event": f"Malware activity on {hostname}"}],
            "iocs": {"hostnames": [hostname]},
            "confidence": 0.85,
            "risk_assessment": "CRITICAL - Active malware. Immediate isolation and forensic analysis required.",
            "detailed_summary": f"## Malware Investigation\n\n**Host:** {hostname}\n**Activity:** {action}\n**Technique:** MITRE ATT&CK T1204\n\nImmediate containment required.",
        }

    def _investigate_generic(self, alert: Dict, evidence: Dict, events: List) -> Dict:
        return {
            "summary": f"Security alert: {alert.get('title', 'Unknown alert')}",
            "root_cause": "Investigation in progress. Additional data needed for root cause determination.",
            "affected_systems": [{"type": "unknown", "identifier": "TBD", "risk": alert.get("severity", "medium")}],
            "attack_path": "Insufficient data to reconstruct attack path.",
            "timeline": [{"time": "Now", "event": "Alert generated"}],
            "iocs": {},
            "confidence": 0.5,
            "risk_assessment": f"Risk level: {alert.get('severity', 'medium').upper()} - Further investigation required.",
            "detailed_summary": f"## Alert Investigation\n\n{alert.get('description', 'No description available.')}",
        }
