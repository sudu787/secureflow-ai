"""
SecureFlow AI - Reporting Agent
Generates executive reports, technical reports, incident summaries, and post-incident reviews.
Uses Grok (xAI) AI for rich narrative reports with template fallback.
LLM Provider: xAI Grok
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from app.agents.base_agent import BaseAgent


class ReportingAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.name = "reporting_agent"
        self.description = "Generates executive and technical reports for incidents"
        self.capabilities = [
            "executive_report",
            "technical_report",
            "incident_summary",
            "post_incident_review",
        ]
        self.llm_provider = "groq"  # Reporting uses Groq

    def get_system_prompt(self) -> str:
        return (
            "You are a Senior Security Reporting & Communications Analyst AI agent "
            "in SecureFlow AI.\n\n"
            "## YOUR ROLE\n"
            "Generate professional, publication-quality incident reports for two audiences:\n\n"
            "### EXECUTIVE REPORT (C-Suite / Board)\n"
            "- Non-technical, business-impact focused\n"
            "- Include: Incident Summary, Business Impact, Risk Level (with color coding), "
            "Actions Taken, Regulatory Implications, Recommendations, Status\n"
            "- Reference compliance frameworks: SOC 2, ISO 27001, NIST CSF, GDPR where applicable\n"
            "- Tone: Professional, concise, reassuring but honest\n\n"
            "### TECHNICAL REPORT (SOC / Engineering)\n"
            "- Deeply technical with full forensic detail\n"
            "- Include: MITRE ATT&CK mapping, Detection Method, Root Cause Analysis, "
            "Attack Kill Chain, Timeline (as markdown table), IOCs (formatted for SIEM import), "
            "Evidence, Remediation with exact commands, Firewall Rules\n"
            "- Tone: Precise, evidence-cited, methodical\n\n"
            "## RULES\n"
            "- Use proper markdown with # headings, ## sections, tables, and ```bash code blocks\n"
            "- NEVER make unsubstantiated claims\n"
            "- NEVER claim actions were taken — use 'recommended' or 'pending execution'\n"
            "- Include confidence scores for all assessments\n"
            "- Respond with valid JSON only\n"
        )

    def process(self, input_data: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        alert = input_data.get("alert", {})
        investigation = input_data.get("investigation", {})
        remediation = input_data.get("remediation", {})
        triage = input_data.get("triage", {})

        # Try Gemini AI for rich narrative reports
        ai_result = self._report_with_ai(alert, investigation, remediation, triage)
        if ai_result:
            ai_result["ai_powered"] = True
            ai_result.setdefault("confidence", 0.90)
            ai_result.setdefault("generated_at", datetime.utcnow().isoformat())
            return ai_result

        # Fallback to template-based reports
        executive_report = self._generate_executive(alert, investigation, remediation, triage)
        technical_report = self._generate_technical(alert, investigation, remediation, triage)

        return {
            "executive_report": executive_report,
            "technical_report": technical_report,
            "confidence": 0.90,
            "generated_at": datetime.utcnow().isoformat(),
            "ai_powered": False,
        }

    def _report_with_ai(self, alert: Dict, investigation: Dict, remediation: Dict, triage: Dict) -> Optional[Dict]:
        """Use Gemini to generate rich narrative reports."""
        prompt = (
            f"Generate a professional executive report AND technical incident report.\n\n"
            f"## Incident Data:\n"
            f"Alert: {alert.get('title', 'Unknown')}\n"
            f"Type: {alert.get('alert_type', 'unknown')}\n"
            f"Severity: {alert.get('severity', 'medium')}\n"
            f"MITRE: {alert.get('mitre_id', 'N/A')} ({alert.get('mitre_tactic', 'N/A')})\n"
            f"Source IP: {alert.get('source_ip', 'N/A')}\n"
            f"Dest IP: {alert.get('dest_ip', 'N/A')}\n"
            f"Priority: {triage.get('priority', 'N/A')}\n\n"
            f"## Investigation Results:\n"
            f"What happened: {investigation.get('what_happened', 'N/A')}\n"
            f"Root cause: {investigation.get('why_it_happened', 'N/A')}\n"
            f"Risk: {investigation.get('risk_assessment', 'N/A')}\n"
            f"IOCs: {json.dumps(investigation.get('iocs', {}), default=str)[:300]}\n\n"
            f"## Remediation:\n"
            f"Summary: {remediation.get('remediation_summary', 'N/A')[:300]}\n"
            f"Automated actions: {json.dumps(remediation.get('automated_actions', []))}\n\n"
            f"Respond with JSON containing two fields:\n"
            f'{{\n'
            f'  "executive_report": "Full markdown executive report with # title, ## sections for Summary, Impact, Risk, Actions Taken, Recommendations, Status. Non-technical, business-focused.",\n'
            f'  "technical_report": "Full markdown technical report with # title, ## sections for MITRE ATT&CK, Detection Details, Root Cause, Attack Path, Timeline (as markdown table), IOCs, Evidence, Remediation, Firewall Rules (as ```bash code blocks). Detailed and technical."\n'
            f'}}'
        )

        result = self.call_llm_json(prompt)
        if result and "executive_report" in result:
            return result
        return None

    def _generate_executive(self, alert, investigation, remediation, triage) -> str:
        title = alert.get("title", "Security Incident")
        severity = alert.get("severity", "medium").upper()
        priority = triage.get("priority", "P3")

        report = f"""# Executive Incident Report

## Incident: {title}

**Severity:** {severity} | **Priority:** {priority} | **Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

---

## Summary

{investigation.get('what_happened', 'A security incident has been detected and investigated by the SecureFlow AI system.')}

## Impact Assessment

{triage.get('impact_assessment', 'Impact assessment in progress.')}

## Risk Level

{investigation.get('risk_assessment', 'Risk assessment pending.')}

## Actions Taken

{self._format_remediation_summary(remediation)}

## Recommendations

{self._format_recommendations(remediation)}

## Status

- **Detection:** ✅ Automated detection by SecureFlow AI
- **Investigation:** ✅ AI-powered investigation complete
- **Remediation:** 🔄 Plan generated, awaiting execution
- **Verification:** ⏳ Pending post-remediation verification

---

*Report generated by SecureFlow AI Reporting Agent*
*Confidence Level: {triage.get('confidence', 0.8):.0%}*
"""
        return report

    def _generate_technical(self, alert, investigation, remediation, triage) -> str:
        title = alert.get("title", "Security Incident")
        evidence = alert.get("evidence", {})
        mitre_id = alert.get("mitre_id", "N/A")
        mitre_tactic = alert.get("mitre_tactic", "N/A")
        mitre_name = alert.get("mitre_technique_name", "N/A")

        report = f"""# Technical Incident Report

## {title}

**MITRE ATT&CK:** {mitre_id} - {mitre_name} ({mitre_tactic})
**Alert Type:** {alert.get('alert_type', 'N/A')}
**Confidence:** {alert.get('confidence', 0):.0%}
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

---

## Detection Details

- **Detection Method:** Rule-based + Behavioral analysis
- **Source IP:** {alert.get('source_ip', 'N/A')}
- **Target:** {alert.get('dest_ip', 'N/A')}
- **Affected Assets:** {', '.join(alert.get('affected_assets', ['N/A']))}

## Root Cause Analysis

{investigation.get('why_it_happened', 'Root cause analysis in progress.')}

## Attack Path

{investigation.get('attack_path', 'Attack path reconstruction in progress.')}

## Timeline

{self._format_timeline(investigation.get('timeline', []))}

## Indicators of Compromise (IOCs)

{self._format_iocs(investigation.get('iocs', {}))}

## Evidence

```json
{self._format_evidence(evidence)}
```

## Remediation Plan

{remediation.get('remediation_summary', 'Remediation plan pending.')}

## Firewall Rules

{self._format_firewall_rules(remediation.get('firewall_rules', []))}

---

*Technical report generated by SecureFlow AI*
"""
        return report

    def _format_remediation_summary(self, remediation: Dict) -> str:
        actions = remediation.get("automated_actions", [])
        if actions:
            return "\n".join(f"- {a}" for a in actions)
        return "- Remediation plan has been generated and is awaiting execution"

    def _format_recommendations(self, remediation: Dict) -> str:
        hardening = remediation.get("hardening_recommendations", [])
        if hardening:
            return "\n".join(f"- {h}" for h in hardening[:5])
        return "- Review and implement security hardening recommendations"

    def _format_timeline(self, timeline: list) -> str:
        if not timeline:
            return "| Time | Event |\n|------|-------|\n| N/A | Timeline pending |"
        rows = "| Time | Event |\n|------|-------|\n"
        for entry in timeline:
            rows += f"| {entry.get('time', 'N/A')} | {entry.get('event', 'N/A')} |\n"
        return rows

    def _format_iocs(self, iocs: Dict) -> str:
        if not iocs:
            return "No IOCs extracted yet."
        lines = []
        for key, value in iocs.items():
            if isinstance(value, list):
                lines.append(f"- **{key}:** {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"- **{key}:** {value}")
        return "\n".join(lines)

    def _format_evidence(self, evidence: Dict) -> str:
        try:
            return json.dumps(evidence, indent=2, default=str)[:1000]
        except Exception:
            return str(evidence)[:1000]

    def _format_firewall_rules(self, rules: list) -> str:
        if not rules:
            return "No firewall rules generated."
        return "\n\n".join(f"```bash\n{rule}\n```" for rule in rules)
