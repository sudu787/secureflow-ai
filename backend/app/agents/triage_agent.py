"""
SecureFlow AI - Triage Agent
Determines severity, assigns priority (P1-P4), and detects false positives.
Uses Gemini AI for intelligent triage with heuristic fallback.
LLM Provider: Google Gemini
"""

import json
from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent


class TriageAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.name = "triage_agent"
        self.description = "Determines severity, assigns priority, and detects false positives"
        self.capabilities = [
            "severity_classification",
            "priority_assignment",
            "false_positive_detection",
            "alert_deduplication",
        ]
        self.llm_provider = "groq"  # Triage uses Groq
        self.max_tokens = 1024  # Triage responses are short

    def get_system_prompt(self) -> str:
        return (
            "You are a Senior SOC Triage Analyst AI agent in SecureFlow AI, "
            "an enterprise-grade autonomous security operations platform.\n\n"
            "## YOUR ROLE\n"
            "Triage incoming security alerts with the precision of a 10-year SOC veteran.\n\n"
            "## TRIAGE CRITERIA\n"
            "1. **Priority Assignment**: P1=Critical (active breach, data exfiltration), "
            "P2=High (exploitation attempt, lateral movement), P3=Medium (reconnaissance, "
            "policy violation), P4=Low (informational, noise)\n"
            "2. **False Positive Assessment**: Score 0.0 (definitely real) to 1.0 (definitely FP). "
            "Consider: internal vs external IP, event count, time of day, user role, "
            "historical patterns, and detection confidence.\n"
            "3. **Impact Assessment**: Number of affected assets, criticality of assets, "
            "potential for data loss, business disruption potential.\n"
            "4. **MITRE ATT&CK Mapping**: Always map findings to specific technique IDs.\n\n"
            "## RULES\n"
            "- NEVER claim 100% certainty. Use confidence scores.\n"
            "- NEVER claim you have taken actions (blocked, quarantined, etc). You can only recommend.\n"
            "- Always provide evidence for your triage decision.\n"
            "- Respond ONLY with valid JSON. No markdown, no explanation outside JSON.\n\n"
            "## FEW-SHOT EXAMPLE\n"
            "Input: SSH brute force, 15 failed attempts from 185.220.101.34, confidence 0.92\n"
            "Output: {\"priority\":\"P2\",\"severity\":\"high\",\"false_positive_score\":0.1,"
            "\"false_positive_reason\":\"External IP with high attempt count indicates real attack\","
            "\"is_false_positive\":false,\"impact_assessment\":\"HIGH - External attacker targeting "
            "SSH authentication. 1 server at risk of unauthorized access.\","
            "\"confidence\":0.92,\"recommended_action\":\"Block source IP. Reset passwords for "
            "targeted accounts. Enable MFA. Review SSH hardening.\","
            "\"triage_summary\":\"SSH brute force from known malicious IP. P2 priority.\"}"
        )

    def process(self, input_data: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        alert = input_data.get("alert", {})
        severity = alert.get("severity", "medium")
        confidence = alert.get("confidence", 0.5)
        alert_type = alert.get("alert_type", "unknown")
        evidence = alert.get("evidence", {})

        # Try Gemini AI first
        ai_result = self._triage_with_ai(alert, evidence)
        if ai_result:
            ai_result["ai_powered"] = True
            return ai_result

        # Fallback to heuristic logic
        priority = self._assign_priority(severity, confidence, alert_type)
        fp_score, fp_reason = self._assess_false_positive(alert, evidence)
        impact = self._assess_impact(alert)

        return {
            "priority": priority,
            "severity": severity,
            "false_positive_score": fp_score,
            "false_positive_reason": fp_reason,
            "is_false_positive": fp_score > 0.7,
            "impact_assessment": impact,
            "confidence": confidence,
            "recommended_action": self._get_recommended_action(priority, fp_score),
            "triage_summary": (
                f"Alert '{alert.get('title', 'Unknown')}' triaged as {priority} "
                f"(severity: {severity}, confidence: {confidence:.0%}). "
                f"False positive probability: {fp_score:.0%}. "
                f"{impact}"
            ),
            "mitre_mapping": {
                "technique_id": alert.get("mitre_id", "N/A"),
                "tactic": alert.get("mitre_tactic", "N/A"),
                "technique_name": alert.get("mitre_technique_name", "N/A"),
            },
            "ai_powered": False,
        }

    def _triage_with_ai(self, alert: Dict, evidence: Dict) -> Optional[Dict]:
        """Use Gemini to perform intelligent triage."""
        prompt = (
            f"Triage this security alert and respond with JSON:\n\n"
            f"Alert Title: {alert.get('title', 'Unknown')}\n"
            f"Alert Type: {alert.get('alert_type', 'unknown')}\n"
            f"Severity: {alert.get('severity', 'medium')}\n"
            f"Confidence: {alert.get('confidence', 0.5)}\n"
            f"Source IP: {alert.get('source_ip', 'N/A')}\n"
            f"Dest IP: {alert.get('dest_ip', 'N/A')}\n"
            f"MITRE Technique: {alert.get('mitre_id', 'N/A')} - {alert.get('mitre_tactic', 'N/A')}\n"
            f"Description: {alert.get('description', 'N/A')}\n"
            f"Evidence: {json.dumps(evidence, default=str)[:500]}\n\n"
            f"Respond with this exact JSON structure:\n"
            f'{{\n'
            f'  "priority": "P1|P2|P3|P4",\n'
            f'  "severity": "critical|high|medium|low",\n'
            f'  "false_positive_score": 0.0-1.0,\n'
            f'  "false_positive_reason": "explanation",\n'
            f'  "is_false_positive": true|false,\n'
            f'  "impact_assessment": "detailed impact description",\n'
            f'  "confidence": 0.0-1.0,\n'
            f'  "recommended_action": "what to do next",\n'
            f'  "triage_summary": "concise triage summary"\n'
            f'}}'
        )

        result = self.call_llm_json(prompt)
        if result and "priority" in result:
            # Ensure required fields
            result.setdefault("mitre_mapping", {
                "technique_id": alert.get("mitre_id", "N/A"),
                "tactic": alert.get("mitre_tactic", "N/A"),
                "technique_name": alert.get("mitre_technique_name", "N/A"),
            })
            result.setdefault("confidence", alert.get("confidence", 0.8))
            return result
        return None

    def _assign_priority(self, severity: str, confidence: float, alert_type: str) -> str:
        severity_weight = {
            "critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0
        }
        score = severity_weight.get(severity, 1) * confidence

        high_risk_types = ["privilege_escalation", "malware_activity", "suspicious_powershell"]
        if alert_type in high_risk_types:
            score *= 1.3

        if score >= 3.0:
            return "P1"
        elif score >= 2.0:
            return "P2"
        elif score >= 1.0:
            return "P3"
        else:
            return "P4"

    def _assess_false_positive(self, alert: Dict, evidence: Dict) -> tuple:
        fp_score = 0.1
        reasons = []

        confidence = alert.get("confidence", 0.5)
        if confidence < 0.5:
            fp_score += 0.3
            reasons.append("Low detection confidence")
        elif confidence < 0.7:
            fp_score += 0.15
            reasons.append("Moderate detection confidence")

        event_count = evidence.get("failed_attempts", evidence.get("unique_ports", 1))
        if event_count <= 2:
            fp_score += 0.2
            reasons.append("Very few supporting events")

        source_ip = alert.get("source_ip", "")
        if source_ip.startswith("10.") or source_ip.startswith("192.168.") or source_ip.startswith("172."):
            fp_score += 0.1
            reasons.append("Internal IP address")

        fp_score = min(fp_score, 0.95)
        reason = "; ".join(reasons) if reasons else "No false positive indicators"
        return round(fp_score, 2), reason

    def _assess_impact(self, alert: Dict) -> str:
        severity = alert.get("severity", "medium")
        assets = alert.get("affected_assets", [])
        impact_map = {
            "critical": f"CRITICAL impact - {len(assets)} assets at risk. Immediate response required.",
            "high": f"HIGH impact - {len(assets)} assets potentially compromised. Urgent investigation needed.",
            "medium": f"MEDIUM impact - {len(assets)} assets may be affected. Investigation recommended.",
            "low": f"LOW impact - {len(assets)} assets flagged. Monitor and review.",
        }
        return impact_map.get(severity, f"Unknown impact - {len(assets)} assets involved.")

    def _get_recommended_action(self, priority: str, fp_score: float) -> str:
        if fp_score > 0.7:
            return "Mark as potential false positive. Verify with asset owner before closing."
        actions = {
            "P1": "IMMEDIATE: Escalate to senior analyst. Begin incident response procedures.",
            "P2": "URGENT: Assign to analyst for investigation within 1 hour.",
            "P3": "STANDARD: Queue for investigation within 4 hours.",
            "P4": "LOW: Review during next scheduled triage session.",
        }
        return actions.get(priority, "Review and assess.")
