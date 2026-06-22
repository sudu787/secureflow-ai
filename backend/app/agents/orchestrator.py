"""
SecureFlow AI - Agent Orchestrator
Central coordinator for the multi-agent system.
Routes requests, manages handoffs, and aggregates results.
Uses a supervisor pattern to coordinate specialized agents.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.agents.triage_agent import TriageAgent
from app.agents.investigation_agent import InvestigationAgent
from app.agents.remediation_agent import RemediationAgent
from app.agents.it_support_agent import ITSupportAgent
from app.agents.reporting_agent import ReportingAgent
from app.models.agent_action import AgentAction
from app.models.alert import Alert
from app.models.ticket import Ticket
from app.models.incident import Incident


class Orchestrator:
    """
    Central orchestrator that coordinates all specialized agents.
    Implements the Supervisor pattern for multi-agent coordination.
    """

    def __init__(self):
        self.triage = TriageAgent()
        self.investigation = InvestigationAgent()
        self.remediation = RemediationAgent()
        self.it_support = ITSupportAgent()
        self.reporting = ReportingAgent()

    def classify_request(self, message: str) -> str:
        """Classify user request to route to appropriate agent."""
        message_lower = message.lower()

        # IT Support keywords
        it_keywords = [
            "vpn", "email", "printer", "slow", "can't login", "password",
            "locked out", "install", "software", "not working", "help",
            "outlook", "wifi", "internet", "laptop", "computer", "phone",
            "teams", "zoom", "application", "error", "crash", "update",
        ]

        # Security keywords
        security_keywords = [
            "alert", "threat", "attack", "breach", "malware", "virus",
            "suspicious", "incident", "investigate", "vulnerability",
            "exploit", "intrusion", "scan", "brute force", "firewall",
            "compromise", "unauthorized", "anomaly", "phishing",
        ]

        # Reporting keywords
        report_keywords = [
            "report", "summary", "overview", "status", "metrics",
            "executive", "technical", "review", "analysis",
        ]

        it_score = sum(1 for kw in it_keywords if kw in message_lower)
        sec_score = sum(1 for kw in security_keywords if kw in message_lower)
        rep_score = sum(1 for kw in report_keywords if kw in message_lower)

        if it_score > sec_score and it_score > rep_score:
            return "it_support"
        elif sec_score > 0:
            return "security"
        elif rep_score > 0:
            return "reporting"
        else:
            return "general"

    def handle_chat_message(self, message: str, session_type: str = "general", db: Session = None, chat_history: str = "") -> Dict[str, Any]:
        """Handle an incoming chat message by routing to the appropriate agent."""
        start_time = time.time()

        # Classify the request
        if session_type == "it_support":
            category = "it_support"
        elif session_type == "security":
            category = "security"
        else:
            category = self.classify_request(message)

        result = {}

        if category == "it_support":
            agent_result = self.it_support.execute({"message": message, "chat_history": chat_history})
            agent_name = "it_support_agent"
            response = agent_result.get("result", {}).get("response", "I can help with that. Could you provide more details?")
            confidence = agent_result.get("confidence", 0.5)

            # Auto-create ticket if applicable
            ticket_id = None
            if db and agent_result.get("result", {}).get("should_create_ticket"):
                ticket_id = self._create_support_ticket(db, message, agent_result.get("result", {}))

            result = {
                "response": response,
                "agent_used": agent_name,
                "confidence": confidence,
                "actions_taken": [f"IT issue diagnosed as: {agent_result.get('result', {}).get('category', 'general')}"],
                "ticket_created": ticket_id,
            }

        elif category == "security":
            # Route through investigation agent for AI-powered security analysis
            agent_result = self.investigation.execute({
                "alert": {"title": message, "description": message, "severity": "medium"},
                "triage": {"priority": "P3"},
                "related_events": [],
                "chat_history": chat_history,
            })
            ai_response = agent_result.get("result", {}).get("detailed_summary", "")
            if ai_response and agent_result.get("ai_powered"):
                response = (
                    f"## 🔒 AI Security Analysis\n\n{ai_response}\n\n"
                    f"**What happened:** {agent_result.get('result', {}).get('what_happened', 'N/A')}\n\n"
                    f"**Risk Assessment:** {agent_result.get('result', {}).get('risk_assessment', 'N/A')}\n\n"
                    f"*Powered by AI Investigation Agent*"
                )
                confidence = agent_result.get("confidence", 0.85)
            else:
                response = self._handle_security_query(message, db)
                confidence = 0.85
            result = {
                "response": response,
                "agent_used": "investigation_agent",
                "confidence": confidence,
                "actions_taken": ["Security query analyzed by AI"],
            }

        elif category == "reporting":
            # Route through reporting agent for AI-powered reports
            agent_result = self.reporting.execute({
                "alert": {"title": message, "description": message},
                "triage": {},
                "investigation": {},
                "remediation": {},
                "chat_history": chat_history,
            })
            ai_response = agent_result.get("result", {}).get("executive_report", "")
            if ai_response and agent_result.get("ai_powered"):
                response = f"## 📊 AI-Generated Report\n\n{ai_response}"
                confidence = agent_result.get("confidence", 0.90)
            else:
                response = self._handle_report_request(message, db)
                confidence = 0.90
            result = {
                "response": response,
                "agent_used": "reporting_agent",
                "confidence": confidence,
                "actions_taken": ["Report generated by AI"],
            }

        else:
            # General greeting — include live stats if available
            stats_text = ""
            if db:
                try:
                    from app.models.alert import Alert as AlertModel
                    from app.models.incident import Incident as IncidentModel
                    open_alerts = db.query(AlertModel).filter(AlertModel.status == "open").count()
                    open_incidents = db.query(IncidentModel).filter(IncidentModel.status.in_(["open", "investigating"])).count()
                    stats_text = (
                        f"\n\n📈 **Current Status:**\n"
                        f"- {open_alerts} open alert(s)\n"
                        f"- {open_incidents} active incident(s)\n"
                    )
                except Exception:
                    pass

            response = (
                "I'm SecureFlow AI, your security operations and IT support assistant. "
                "I can help you with:\n\n"
                "🔒 **Security Operations**\n"
                "- Investigate security alerts and incidents\n"
                "- Analyze threats and provide MITRE ATT&CK mappings\n"
                "- Generate remediation plans\n\n"
                "🔧 **IT Support**\n"
                "- Troubleshoot VPN, email, and printer issues\n"
                "- Diagnose slow computer performance\n"
                "- Help with account lockouts and password resets\n\n"
                "📊 **Reporting**\n"
                "- Generate executive incident summaries\n"
                "- Create technical investigation reports\n"
                f"{stats_text}\n"
                "How can I assist you today?"
            )
            result = {
                "response": response,
                "agent_used": "orchestrator",
                "confidence": 1.0,
                "actions_taken": [],
            }

        # Log agent action
        if db:
            self._log_action(db, result.get("agent_used", "orchestrator"), "chat_response",
                           message[:200], response[:200] if isinstance(response, str) else "Generated",
                           result.get("confidence", 0.5))

        duration_ms = int((time.time() - start_time) * 1000)
        result["processing_time_ms"] = duration_ms
        return result

    def analyze_alert(self, alert_data: Dict, db: Session = None) -> Dict[str, Any]:
        """Run full analysis pipeline: Triage → Investigate → Remediate → Report."""
        start_time = time.time()
        results = {}
        agent_providers = {}

        # Step 1: Triage (Gemini)
        triage_result = self.triage.execute({"alert": alert_data})
        results["triage"] = triage_result.get("result", {})
        agent_providers["triage"] = {
            "agent": "triage_agent",
            "llm": triage_result.get("llm_provider", "gemini"),
            "ai_powered": triage_result.get("ai_powered", False),
            "duration_ms": triage_result.get("duration_ms", 0),
        }

        # Small delay — agents alternate between Gemini and Grok, so rate limits are distributed
        time.sleep(3)

        # Step 2: Investigation (Grok)
        investigation_result = self.investigation.execute({
            "alert": alert_data,
            "triage": results["triage"],
            "related_events": [],
        })
        results["investigation"] = investigation_result.get("result", {})
        agent_providers["investigation"] = {
            "agent": "investigation_agent",
            "llm": investigation_result.get("llm_provider", "grok"),
            "ai_powered": investigation_result.get("ai_powered", False),
            "duration_ms": investigation_result.get("duration_ms", 0),
        }

        time.sleep(3)

        # Step 3: Remediation (Gemini)
        remediation_result = self.remediation.execute({
            "alert": alert_data,
            "investigation": results["investigation"],
        })
        results["remediation"] = remediation_result.get("result", {})
        agent_providers["remediation"] = {
            "agent": "remediation_agent",
            "llm": remediation_result.get("llm_provider", "gemini"),
            "ai_powered": remediation_result.get("ai_powered", False),
            "duration_ms": remediation_result.get("duration_ms", 0),
        }

        time.sleep(3)

        # Step 4: Report (Grok)
        report_result = self.reporting.execute({
            "alert": alert_data,
            "triage": results["triage"],
            "investigation": results["investigation"],
            "remediation": results["remediation"],
        })
        results["report"] = report_result.get("result", {})
        agent_providers["reporting"] = {
            "agent": "reporting_agent",
            "llm": report_result.get("llm_provider", "grok"),
            "ai_powered": report_result.get("ai_powered", False),
            "duration_ms": report_result.get("duration_ms", 0),
        }

        # Create incident and ticket
        ticket_id = None
        incident_id = None
        if db:
            incident_id = self._create_incident(db, alert_data, results)
            ticket_id = self._create_incident_ticket(db, alert_data, results, incident_id)

            # Log all agent actions
            for agent_name in ["triage", "investigation", "remediation", "reporting"]:
                self._log_action(
                    db, f"{agent_name}_agent", "alert_analysis",
                    alert_data.get("title", "")[:200],
                    f"Completed {agent_name} analysis via {agent_providers.get(agent_name, {}).get('llm', 'unknown')}",
                    results.get(agent_name, {}).get("confidence", 0.5),
                    related_alert_id=alert_data.get("id"),
                    related_ticket_id=ticket_id,
                )

        duration_ms = int((time.time() - start_time) * 1000)

        return {
            "triage": results["triage"],
            "investigation": results["investigation"],
            "remediation": results["remediation"],
            "report": results["report"],
            "incident_id": incident_id,
            "ticket_created": ticket_id,
            "confidence": results["triage"].get("confidence", 0.5),
            "processing_time_ms": duration_ms,
            "agent_providers": agent_providers,
            "multi_llm": True,
        }

    def _handle_security_query(self, message: str, db: Session = None) -> str:
        """Handle general security queries with real data from the database."""
        # Pull live data for context-aware responses
        alert_summary = ""
        if db:
            try:
                recent = db.query(Alert).filter(Alert.status == "open").order_by(Alert.created_at.desc()).limit(5).all()
                if recent:
                    alert_summary = "\n### 🚨 Current Open Alerts\n"
                    for a in recent:
                        mitre = f" ({a.mitre_id})" if a.mitre_id else ""
                        alert_summary += f"- **[{a.severity.upper()}]** {a.title}{mitre} — {a.status}\n"
                    alert_summary += "\n"
                else:
                    alert_summary = "\n✅ **No open alerts** — All systems are currently clear.\n\n"
            except Exception:
                pass

        return (
            f"## 🔒 Security Analysis\n\n"
            f"I've analyzed your security query: *\"{message[:100]}\"*\n\n"
            f"Here's my assessment based on current system data:\n\n"
            f"### Recommendations\n"
            f"1. **Monitor** — Review relevant security logs and active alerts\n"
            f"2. **Investigate** — Check the Alerts dashboard for correlated incidents\n"
            f"3. **Respond** — Follow remediation steps for any active threats\n"
            f"{alert_summary}"
            f"### Next Steps\n"
            f"Navigate to the **Alerts** page and click any alert to run the full "
            f"**AI Investigation Pipeline** (Triage → Investigation → Remediation → Report) "
            f"with MITRE ATT&CK mapping.\n\n"
            f"Would you like me to investigate a specific alert or provide more details?"
        )

    def _handle_report_request(self, message: str, db: Session = None) -> str:
        """Handle report generation requests with real data."""
        report_data = ""
        if db:
            try:
                from app.models.incident import Incident as IncModel
                incidents = db.query(IncModel).order_by(IncModel.created_at.desc()).limit(5).all()
                open_alerts = db.query(Alert).filter(Alert.status == "open").count()
                total_alerts = db.query(Alert).count()
                resolved = db.query(Alert).filter(Alert.status.in_(["resolved", "closed"])).count()

                report_data = (
                    f"\n### 📈 Current Metrics\n"
                    f"- **Total Alerts:** {total_alerts} ({open_alerts} open, {resolved} resolved)\n"
                    f"- **Active Incidents:** {len([i for i in incidents if i.status in ('open', 'investigating')])}\n"
                    f"- **Resolution Rate:** {(resolved/total_alerts*100):.0f}%\n\n" if total_alerts > 0 else
                    "\n### 📈 No data available yet. Run demo scenarios to generate data.\n\n"
                )

                if incidents:
                    report_data += "### Recent Incidents\n"
                    for inc in incidents[:3]:
                        report_data += f"- **#{inc.id}** {inc.title} — [{inc.severity}/{inc.status}]\n"
                    report_data += "\n"
            except Exception:
                pass

        return (
            f"## 📊 Security Operations Report\n\n"
            f"Report generated for your request: *\"{message[:100]}\"*\n"
            f"{report_data}"
            f"### Available Reports\n"
            f"1. **Executive Summary** — High-level incident overview for leadership\n"
            f"2. **Technical Report** — Detailed technical analysis with IOCs and MITRE mappings\n"
            f"3. **Incident Timeline** — Chronological event reconstruction\n"
            f"4. **Remediation Status** — Current status of remediation actions\n\n"
            f"To generate a detailed AI report for a specific incident, navigate to the "
            f"**Alerts** page, select an alert, and click **🤖 Run AI Investigation**."
        )

    def _create_support_ticket(self, db: Session, message: str, result: Dict) -> Optional[int]:
        try:
            ticket = Ticket(
                title=f"IT Support: {result.get('category', 'General').title()} Issue",
                description=message[:500],
                category=result.get("category", "other"),
                priority="P3",
                status="open",
                source="ai_agent",
                requester="user",
                diagnosis=result.get("response", "")[:1000],
                timeline=[{
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "Ticket created by AI agent",
                    "actor": "SecureFlow AI",
                }],
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            return ticket.id
        except Exception:
            db.rollback()
            return None

    def _create_incident(self, db: Session, alert_data: Dict, results: Dict) -> Optional[int]:
        try:
            incident = Incident(
                title=f"Incident: {alert_data.get('title', 'Security Incident')}",
                description=results["investigation"].get("what_happened", ""),
                severity=alert_data.get("severity", "medium"),
                priority=results["triage"].get("priority", "P3"),
                status="investigating",
                related_alert_ids=[alert_data.get("id")] if alert_data.get("id") else [],
                investigation_results=results["investigation"],
                root_cause=results["investigation"].get("why_it_happened", ""),
                attack_path=results["investigation"].get("attack_path", ""),
                affected_systems=results["investigation"].get("affected_systems", []),
                remediation_plan=results["remediation"],
                assigned_to="SecureFlow AI",
                executive_summary=results["report"].get("executive_report", ""),
                technical_summary=results["report"].get("technical_report", ""),
            )
            db.add(incident)
            db.commit()
            db.refresh(incident)
            return incident.id
        except Exception:
            db.rollback()
            return None

    def _create_incident_ticket(self, db: Session, alert_data: Dict, results: Dict, incident_id: int = None) -> Optional[int]:
        try:
            ticket = Ticket(
                title=f"Security Incident: {alert_data.get('title', 'Alert')}",
                description=results["investigation"].get("what_happened", ""),
                category="security_incident",
                priority=results["triage"].get("priority", "P3"),
                status="open",
                source="ai_agent",
                related_incident_id=incident_id,
                related_alert_id=alert_data.get("id"),
                diagnosis=results["investigation"].get("detailed_summary", ""),
                timeline=[{
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "Ticket auto-created from security alert analysis",
                    "actor": "SecureFlow AI Orchestrator",
                }],
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            return ticket.id
        except Exception:
            db.rollback()
            return None

    def _log_action(self, db: Session, agent_name: str, action_type: str,
                    input_summary: str, output_summary: str, confidence: float,
                    related_alert_id: int = None, related_ticket_id: int = None):
        try:
            action = AgentAction(
                agent_name=agent_name,
                action_type=action_type,
                input_summary=input_summary,
                output_summary=output_summary,
                confidence=confidence,
                status="completed",
                related_alert_id=related_alert_id,
                related_ticket_id=related_ticket_id,
            )
            db.add(action)
            db.commit()
        except Exception:
            db.rollback()
