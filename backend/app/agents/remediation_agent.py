"""
SecureFlow AI - Remediation Agent
Generates remediation plans, firewall rules, and security recommendations.
Uses Gemini AI for context-aware remediation with heuristic fallback.
LLM Provider: Google Gemini
"""

import json
from typing import Dict, Any, Optional, List
from app.agents.base_agent import BaseAgent


class RemediationAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.name = "remediation_agent"
        self.description = "Generates remediation plans, firewall rules, and security recommendations"
        self.capabilities = [
            "remediation_planning",
            "firewall_rule_generation",
            "security_hardening",
            "playbook_execution",
        ]
        self.llm_provider = "groq"  # Remediation uses Groq

    def get_system_prompt(self) -> str:
        return (
            "You are a Senior Security Remediation Engineer AI agent in SecureFlow AI, "
            "an enterprise-grade autonomous security operations platform.\n\n"
            "## YOUR ROLE\n"
            "Generate precise, actionable, CIS Benchmark-aligned remediation plans. "
            "Your plans must be immediately executable by a junior SOC analyst.\n\n"
            "## REMEDIATION FRAMEWORK\n"
            "1. **Immediate Containment**: Stop the active threat (block IP, isolate host, disable account)\n"
            "2. **Evidence Preservation**: Ensure forensic evidence is captured before remediation\n"
            "3. **Eradication**: Remove the threat (malware, backdoors, unauthorized access)\n"
            "4. **Recovery**: Restore systems to known-good state\n"
            "5. **Hardening**: Prevent recurrence (patch, harden, update policies)\n\n"
            "## PLATFORM-SPECIFIC COMMANDS\n"
            "- Linux: iptables, ufw, fail2ban, systemctl, auditd\n"
            "- Windows: netsh, Get-WinEvent, Set-MpPreference, Windows Defender, GPO\n"
            "- Network: ACL rules, VLAN isolation, DNS sinkhole\n\n"
            "## RULES\n"
            "- NEVER claim you have executed any commands. You RECOMMEND commands.\n"
            "- Always include rollback procedures for destructive actions\n"
            "- Provide estimated time for each remediation step\n"
            "- Include CIS Benchmark references where applicable\n"
            "- Respond with valid JSON only\n"
        )

    def process(self, input_data: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        alert = input_data.get("alert", {})
        investigation = input_data.get("investigation", {})
        alert_type = alert.get("alert_type", "unknown")

        # Try Gemini AI first
        ai_result = self._remediate_with_ai(alert, investigation)
        if ai_result:
            ai_result["ai_powered"] = True
            return ai_result

        # Fallback to heuristic logic
        plan = self._generate_plan(alert_type, alert, investigation)

        return {
            "remediation_plan": plan["steps"],
            "firewall_rules": plan["firewall_rules"],
            "hardening_recommendations": plan["hardening"],
            "automated_actions": plan["automated_actions"],
            "priority": plan["priority"],
            "estimated_time": plan["estimated_time"],
            "confidence": plan["confidence"],
            "remediation_summary": plan["summary"],
            "ai_powered": False,
        }

    def _remediate_with_ai(self, alert: Dict, investigation: Dict) -> Optional[Dict]:
        """Use Gemini for context-aware remediation planning."""
        prompt = (
            f"Generate a detailed remediation plan for this security incident. Respond with JSON.\n\n"
            f"Alert: {alert.get('title', 'Unknown')}\n"
            f"Type: {alert.get('alert_type', 'unknown')}\n"
            f"Severity: {alert.get('severity', 'medium')}\n"
            f"Source IP: {alert.get('source_ip', 'N/A')}\n"
            f"Dest IP: {alert.get('dest_ip', 'N/A')}\n"
            f"MITRE: {alert.get('mitre_id', 'N/A')} - {alert.get('mitre_tactic', 'N/A')}\n"
            f"Root Cause: {investigation.get('why_it_happened', 'N/A')}\n"
            f"Risk Assessment: {investigation.get('risk_assessment', 'N/A')}\n"
            f"IOCs: {json.dumps(investigation.get('iocs', {}), default=str)[:400]}\n\n"
            f"Respond with this JSON structure:\n"
            f'{{\n'
            f'  "remediation_plan": [{{"order": 1, "action": "specific action", "urgency": "immediate|high|medium|low", "automated": true|false}}],\n'
            f'  "firewall_rules": ["# Comment\\niptables command or ufw command"],\n'
            f'  "hardening_recommendations": ["specific hardening step"],\n'
            f'  "automated_actions": ["action that can be automated"],\n'
            f'  "priority": "P1|P2|P3|P4",\n'
            f'  "estimated_time": "time estimate",\n'
            f'  "confidence": 0.0-1.0,\n'
            f'  "remediation_summary": "full markdown remediation plan with ## headings, ### steps, and ```bash code blocks for commands"\n'
            f'}}'
        )

        result = self.call_llm_json(prompt)
        if result and "remediation_plan" in result:
            result.setdefault("confidence", 0.88)
            return result
        return None

    def _generate_plan(self, alert_type: str, alert: Dict, investigation: Dict) -> Dict:
        generators = {
            "ssh_brute_force": self._plan_brute_force,
            "port_scan": self._plan_port_scan,
            "suspicious_powershell": self._plan_powershell,
            "privilege_escalation": self._plan_privesc,
            "malware_activity": self._plan_malware,
            "failed_login_burst": self._plan_brute_force,
        }
        generator = generators.get(alert_type, self._plan_generic)
        return generator(alert, investigation)

    def _plan_brute_force(self, alert: Dict, investigation: Dict) -> Dict:
        source_ip = alert.get("source_ip", "unknown")
        evidence = alert.get("evidence", {})
        targets = evidence.get("target_users", [])
        return {
            "steps": [
                {"order": 1, "action": f"Block source IP {source_ip} at the firewall", "urgency": "immediate", "automated": True},
                {"order": 2, "action": "Force password reset for all targeted accounts", "urgency": "immediate", "automated": False},
                {"order": 3, "action": "Enable account lockout policy (5 attempts / 15 min)", "urgency": "high", "automated": False},
                {"order": 4, "action": "Enable Multi-Factor Authentication (MFA) for SSH", "urgency": "high", "automated": False},
                {"order": 5, "action": "Review SSH configuration for key-based auth only", "urgency": "medium", "automated": False},
                {"order": 6, "action": "Install fail2ban or equivalent brute force protection", "urgency": "medium", "automated": False},
                {"order": 7, "action": "Review access logs for any successful logins from this IP", "urgency": "high", "automated": True},
            ],
            "firewall_rules": [
                f"# Block attacking IP\niptables -A INPUT -s {source_ip} -j DROP",
                f"# Rate limit SSH connections\niptables -A INPUT -p tcp --dport 22 -m connlimit --connlimit-above 3 -j DROP",
                f"# UFW alternative\nufw deny from {source_ip}",
            ],
            "hardening": ["Disable password authentication in SSH (use key-based only)", "Change SSH port from 22 to a non-standard port", "Implement fail2ban with aggressive settings", "Enable MFA for all remote access", "Set up SSH key rotation policy", "Configure account lockout after 5 failed attempts"],
            "automated_actions": [f"Block IP {source_ip} at perimeter firewall", "Generate incident ticket for security team review", "Send notification to system administrators"],
            "priority": "P1",
            "estimated_time": "30 minutes for immediate actions, 2 hours for full hardening",
            "confidence": 0.92,
            "summary": f"## Remediation Plan: SSH Brute Force\n\n### Immediate Actions\n1. **Block IP** {source_ip} at the firewall\n2. **Force password reset** for accounts: {', '.join(targets)}\n3. **Review logs** for successful logins from {source_ip}\n\n### Short-Term Hardening\n- Enable MFA for SSH access\n- Configure fail2ban\n- Implement account lockout policy\n\n### Firewall Rules\n```bash\niptables -A INPUT -s {source_ip} -j DROP\niptables -A INPUT -p tcp --dport 22 -m connlimit --connlimit-above 3 -j DROP\n```",
        }

    def _plan_port_scan(self, alert: Dict, investigation: Dict) -> Dict:
        source_ip = alert.get("source_ip", "unknown")
        return {
            "steps": [{"order": 1, "action": f"Block source IP {source_ip}", "urgency": "high", "automated": True}, {"order": 2, "action": "Review exposed services and close unnecessary ports", "urgency": "high", "automated": False}, {"order": 3, "action": "Enable IDS/IPS rules for port scan detection", "urgency": "medium", "automated": False}],
            "firewall_rules": [f"iptables -A INPUT -s {source_ip} -j DROP"],
            "hardening": ["Close unnecessary ports", "Implement port knocking", "Enable SYN flood protection"],
            "automated_actions": [f"Block IP {source_ip}", "Alert network team"],
            "priority": "P2",
            "estimated_time": "15 minutes for IP block, 1 hour for port review",
            "confidence": 0.85,
            "summary": f"## Remediation: Port Scan\n\n1. Block {source_ip}\n2. Audit open ports\n3. Harden firewall rules",
        }

    def _plan_powershell(self, alert: Dict, investigation: Dict) -> Dict:
        hostname = alert.get("evidence", {}).get("hostname", "unknown")
        return {
            "steps": [{"order": 1, "action": f"Isolate host {hostname} from network immediately", "urgency": "immediate", "automated": True}, {"order": 2, "action": "Capture memory dump for forensic analysis", "urgency": "immediate", "automated": False}, {"order": 3, "action": "Scan host with multiple AV/EDR tools", "urgency": "high", "automated": True}, {"order": 4, "action": "Review PowerShell execution logs", "urgency": "high", "automated": True}, {"order": 5, "action": "Enable PowerShell Constrained Language Mode", "urgency": "medium", "automated": False}, {"order": 6, "action": "Block PowerShell script execution via AppLocker", "urgency": "medium", "automated": False}],
            "firewall_rules": [f"# Isolate host\niptables -A FORWARD -s {hostname} -j DROP\niptables -A FORWARD -d {hostname} -j DROP"],
            "hardening": ["Enable PowerShell Script Block Logging", "Enable Constrained Language Mode", "Deploy AppLocker policies", "Enable AMSI (Anti-Malware Scan Interface)"],
            "automated_actions": [f"Network isolation of {hostname}", "EDR scan initiated", "Forensic capture triggered"],
            "priority": "P1",
            "estimated_time": "1 hour for containment, 4 hours for full investigation",
            "confidence": 0.90,
            "summary": f"## Remediation: Suspicious PowerShell\n\n**CRITICAL:** Isolate {hostname} immediately.\nCapture forensic evidence before remediation.",
        }

    def _plan_privesc(self, alert: Dict, investigation: Dict) -> Dict:
        evidence = alert.get("evidence", {})
        username = evidence.get("username", "unknown")
        hostname = evidence.get("hostname", "unknown")
        return {
            "steps": [{"order": 1, "action": f"Disable account {username} immediately", "urgency": "immediate", "automated": True}, {"order": 2, "action": f"Isolate host {hostname}", "urgency": "immediate", "automated": True}, {"order": 3, "action": "Audit all actions taken with elevated privileges", "urgency": "high", "automated": True}, {"order": 4, "action": "Check for persistence mechanisms (cron jobs, services, startup scripts)", "urgency": "high", "automated": False}, {"order": 5, "action": "Review and restrict sudo/admin permissions", "urgency": "medium", "automated": False}],
            "firewall_rules": [],
            "hardening": ["Implement least-privilege access", "Enable sudo logging", "Restrict SUID binaries", "Deploy PAM controls"],
            "automated_actions": [f"Disable account {username}", f"Isolate {hostname}", "Audit elevated actions"],
            "priority": "P1",
            "estimated_time": "30 minutes for containment, 2 hours for audit",
            "confidence": 0.87,
            "summary": f"## Remediation: Privilege Escalation\n\n1. Disable {username}\n2. Isolate {hostname}\n3. Full audit of elevated actions",
        }

    def _plan_malware(self, alert: Dict, investigation: Dict) -> Dict:
        hostname = alert.get("evidence", {}).get("hostname", "unknown")
        return {
            "steps": [{"order": 1, "action": f"Isolate {hostname} from network", "urgency": "immediate", "automated": True}, {"order": 2, "action": "Run full endpoint scan", "urgency": "immediate", "automated": True}, {"order": 3, "action": "Capture disk image for forensics", "urgency": "high", "automated": False}, {"order": 4, "action": "Identify and block C2 communications", "urgency": "high", "automated": True}, {"order": 5, "action": "Scan all systems for lateral movement indicators", "urgency": "high", "automated": True}, {"order": 6, "action": "Reimage affected system if confirmed", "urgency": "medium", "automated": False}],
            "firewall_rules": [f"# Block all traffic from/to {hostname}\niptables -A FORWARD -s {hostname} -j DROP"],
            "hardening": ["Update all endpoints", "Deploy EDR solution", "Review email filtering", "User security awareness training"],
            "automated_actions": [f"Isolate {hostname}", "Network-wide IOC scan", "Block known C2 indicators"],
            "priority": "P1",
            "estimated_time": "2 hours containment, 8 hours full remediation",
            "confidence": 0.85,
            "summary": f"## Remediation: Malware\n\n**CRITICAL:** Isolate {hostname}. Begin forensic analysis. Scan environment for spread.",
        }

    def _plan_generic(self, alert: Dict, investigation: Dict) -> Dict:
        return {
            "steps": [{"order": 1, "action": "Investigate alert details", "urgency": "medium", "automated": False}, {"order": 2, "action": "Assess scope of impact", "urgency": "medium", "automated": False}, {"order": 3, "action": "Implement appropriate countermeasures", "urgency": "medium", "automated": False}],
            "firewall_rules": [],
            "hardening": ["Review security posture", "Update detection rules"],
            "automated_actions": ["Generate investigation ticket"],
            "priority": "P3",
            "estimated_time": "1-2 hours",
            "confidence": 0.6,
            "summary": "## Remediation Plan\n\nFurther investigation required to determine specific remediation steps.",
        }
