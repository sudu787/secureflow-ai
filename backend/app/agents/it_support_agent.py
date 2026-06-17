"""
SecureFlow AI - IT Support Agent
Troubleshoots user IT issues: VPN, email, printer, performance, accounts, software.
Uses Grok (xAI) AI for intelligent diagnosis with knowledge base fallback.
LLM Provider: xAI Grok
"""

import json
from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent


class ITSupportAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.name = "it_support_agent"
        self.description = "Troubleshoots user IT issues and provides guided fixes"
        self.capabilities = [
            "vpn_troubleshooting",
            "email_troubleshooting",
            "printer_troubleshooting",
            "performance_diagnosis",
            "account_management",
            "software_installation",
        ]
        self.llm_provider = "groq"  # IT Support uses Groq

        self.knowledge_base = {
            "vpn": {
                "symptoms": ["can't connect", "vpn not working", "vpn disconnects", "vpn slow", "vpn error", "vpn timeout"],
                "diagnosis": ["Check if VPN client is up to date", "Verify network connectivity (ping test)", "Check VPN credentials haven't expired", "Verify VPN server is online", "Check if firewall is blocking VPN ports (UDP 500, 4500)"],
                "solutions": [
                    {"step": 1, "action": "Restart the VPN client application", "detail": "Close the VPN client completely and reopen it."},
                    {"step": 2, "action": "Check your internet connection", "detail": "Try opening a website. If no internet, troubleshoot network first."},
                    {"step": 3, "action": "Clear VPN client cache", "detail": "Go to VPN Settings → Advanced → Clear Cache/Logs."},
                    {"step": 4, "action": "Reinstall the VPN client", "detail": "Download the latest version from the IT portal and reinstall."},
                    {"step": 5, "action": "Try an alternate VPN server", "detail": "Switch to a different VPN server region in the settings."},
                ],
                "escalation": "If the issue persists after all steps, escalate to Network Engineering team.",
            },
            "email": {
                "symptoms": ["email not working", "can't send email", "not receiving emails", "email slow", "outlook", "disconnected"],
                "diagnosis": ["Check email server status", "Verify account credentials", "Check mailbox quota", "Verify email client settings", "Check spam/junk filters"],
                "solutions": [
                    {"step": 1, "action": "Restart your email client", "detail": "Close Outlook/email app completely and reopen."},
                    {"step": 2, "action": "Check email via webmail", "detail": "Try logging into webmail to verify if the issue is client-specific."},
                    {"step": 3, "action": "Clear email client cache", "detail": "Outlook: File → Account Settings → Data Files → clear cache."},
                    {"step": 4, "action": "Recreate email profile", "detail": "Control Panel → Mail → Show Profiles → Add new profile."},
                    {"step": 5, "action": "Check mailbox size", "detail": "If mailbox is full, archive old emails to free space."},
                ],
                "escalation": "If unable to resolve, escalate to Email/Exchange admin team.",
            },
            "printer": {
                "symptoms": ["printer not working", "can't print", "printer offline", "print quality", "paper jam"],
                "diagnosis": ["Check printer power and connectivity", "Verify printer is online in system settings", "Check print queue for stuck jobs", "Verify printer drivers are installed", "Check paper and toner levels"],
                "solutions": [
                    {"step": 1, "action": "Check printer power and cables", "detail": "Ensure the printer is powered on and connected to the network."},
                    {"step": 2, "action": "Restart the Print Spooler service", "detail": "Run: services.msc → Print Spooler → Restart."},
                    {"step": 3, "action": "Clear the print queue", "detail": "Devices and Printers → Right-click printer → See what's printing → Cancel All."},
                    {"step": 4, "action": "Remove and re-add the printer", "detail": "Settings → Devices → Printers → Remove device → Add printer."},
                    {"step": 5, "action": "Update printer drivers", "detail": "Download latest drivers from printer manufacturer website."},
                ],
                "escalation": "If hardware issue suspected, escalate to Facilities/Hardware team.",
            },
            "performance": {
                "symptoms": ["slow computer", "laptop slow", "system slow", "freezing", "hanging", "lag"],
                "diagnosis": ["Check CPU and memory usage", "Check disk space", "Check for malware", "Review startup programs", "Check for system updates pending"],
                "solutions": [
                    {"step": 1, "action": "Restart your computer", "detail": "A full restart (not just sleep/hibernate) clears temporary issues."},
                    {"step": 2, "action": "Check Task Manager for resource hogs", "detail": "Ctrl+Shift+Esc → Sort by CPU/Memory → End unnecessary tasks."},
                    {"step": 3, "action": "Free up disk space", "detail": "Run Disk Cleanup (cleanmgr) and remove temporary files."},
                    {"step": 4, "action": "Disable unnecessary startup programs", "detail": "Task Manager → Startup tab → Disable non-essential apps."},
                    {"step": 5, "action": "Run system file checker", "detail": "Open Command Prompt as admin → Run: sfc /scannow"},
                ],
                "escalation": "If performance doesn't improve, may need hardware upgrade. Escalate to Desktop Support.",
            },
            "account": {
                "symptoms": ["locked out", "password reset", "can't login", "account locked", "forgot password", "mfa"],
                "diagnosis": ["Check if account is locked in Active Directory", "Verify password hasn't expired", "Check MFA device status", "Verify VPN connection for remote password changes"],
                "solutions": [
                    {"step": 1, "action": "Wait 30 minutes for auto-unlock", "detail": "Most account lockouts auto-resolve after 30 minutes."},
                    {"step": 2, "action": "Use self-service password reset", "detail": "Go to https://passwordreset.company.com and follow instructions."},
                    {"step": 3, "action": "Check MFA app", "detail": "Ensure your authenticator app is synced and showing correct codes."},
                    {"step": 4, "action": "Contact IT helpdesk for manual unlock", "detail": "Call the IT helpdesk for immediate account unlock."},
                ],
                "escalation": "For persistent account issues, escalate to Identity & Access Management team.",
            },
            "software": {
                "symptoms": ["install software", "application error", "software not working", "update", "crash"],
                "diagnosis": ["Check software compatibility", "Verify system requirements", "Check for conflicting software", "Review error logs"],
                "solutions": [
                    {"step": 1, "action": "Check the Software Center / App Portal", "detail": "Use the company Software Center for approved software installations."},
                    {"step": 2, "action": "Run the installer as Administrator", "detail": "Right-click installer → Run as administrator."},
                    {"step": 3, "action": "Check system requirements", "detail": "Verify your system meets the minimum requirements for the software."},
                    {"step": 4, "action": "Repair the installation", "detail": "Control Panel → Programs → Select app → Repair."},
                    {"step": 5, "action": "Reinstall the application", "detail": "Uninstall completely, restart, then reinstall fresh."},
                ],
                "escalation": "For enterprise software issues, escalate to Application Support team.",
            },
        }

    def get_system_prompt(self) -> str:
        return (
            "You are a Senior IT Support & Service Desk AI agent in SecureFlow AI, "
            "an enterprise-grade autonomous IT operations platform.\n\n"
            "## YOUR ROLE\n"
            "Provide expert-level IT troubleshooting and support with the warmth of a "
            "helpful colleague and the precision of a senior sysadmin.\n\n"
            "## ITIL-ALIGNED WORKFLOW\n"
            "1. **Identify**: Classify the issue category and urgency\n"
            "2. **Diagnose**: Perform systematic root cause analysis\n"
            "3. **Resolve**: Provide step-by-step fix with exact commands/paths\n"
            "4. **Escalate**: If L1 can't resolve, escalate with full context\n"
            "5. **Document**: Create a ticket for tracking and knowledge base\n\n"
            "## SUPPORTED CATEGORIES\n"
            "VPN, Email/Outlook, Printers, Slow Performance, Account Lockouts, "
            "MFA, Software Installation, Network Issues, Security Concerns, "
            "File Access, Browser Issues, Remote Desktop\n\n"
            "## RULES\n"
            "- Be empathetic and professional — never condescending\n"
            "- Provide EXACT commands, menu paths, and keyboard shortcuts\n"
            "- Include both Windows and macOS instructions when applicable\n"
            "- Always offer to create a support ticket\n"
            "- Suggest security best practices when relevant\n"
            "- Format with ## headings, numbered steps, **bold** key items\n"
            "- NEVER claim you have taken actions — you GUIDE the user\n"
            "- Respond with valid JSON only\n"
        )

    def process(self, input_data: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        user_message = input_data.get("message", "")
        category = self._categorize_issue(user_message)

        # Try Gemini AI for rich conversational response
        ai_result = self._support_with_ai(user_message, category)
        if ai_result:
            ai_result["ai_powered"] = True
            ai_result.setdefault("should_create_ticket", True)
            ai_result.setdefault("ticket_category", category or "general")
            return ai_result

        # Fallback to knowledge base
        if category:
            kb = self.knowledge_base[category]
            return {
                "category": category,
                "diagnosis": kb["diagnosis"],
                "suggested_fixes": kb["solutions"],
                "escalation_path": kb["escalation"],
                "confidence": 0.85,
                "response": self._format_response(category, kb, user_message),
                "should_create_ticket": True,
                "ticket_category": category,
                "ai_powered": False,
            }
        else:
            return {
                "category": "general",
                "diagnosis": ["Unable to automatically categorize the issue"],
                "suggested_fixes": [],
                "escalation_path": "Please contact the IT helpdesk for assistance.",
                "confidence": 0.3,
                "response": (
                    "I'd like to help you with your IT issue. Could you provide more details about:\n\n"
                    "1. **What's happening?** (error messages, symptoms)\n"
                    "2. **When did it start?** (after an update, suddenly, gradually)\n"
                    "3. **What have you tried?** (restart, reinstall, etc.)\n\n"
                    "I can help with: VPN, email, printers, slow computers, account lockouts, and software issues."
                ),
                "should_create_ticket": False,
                "ai_powered": False,
            }

    def _support_with_ai(self, user_message: str, category: Optional[str]) -> Optional[Dict]:
        """Use Gemini for conversational IT support."""
        kb_context = ""
        if category and category in self.knowledge_base:
            kb = self.knowledge_base[category]
            kb_context = (
                f"\n\nRelevant knowledge base for '{category}':\n"
                f"Diagnosis steps: {json.dumps(kb['diagnosis'])}\n"
                f"Solutions: {json.dumps(kb['solutions'], default=str)}\n"
                f"Escalation: {kb['escalation']}\n"
            )

        prompt = (
            f"An employee needs IT help. Provide a helpful, detailed troubleshooting response.\n\n"
            f"User's issue: {user_message}\n"
            f"Detected category: {category or 'unknown'}\n"
            f"{kb_context}\n\n"
            f"Respond with this JSON structure:\n"
            f'{{\n'
            f'  "category": "{category or "general"}",\n'
            f'  "diagnosis": ["diagnostic check 1", "diagnostic check 2"],\n'
            f'  "suggested_fixes": [{{"step": 1, "action": "action name", "detail": "detailed instruction"}}],\n'
            f'  "escalation_path": "who to escalate to if unresolved",\n'
            f'  "confidence": 0.0-1.0,\n'
            f'  "response": "Full markdown-formatted response with ## headings, numbered steps, **bold** key items, and specific commands/paths. Be empathetic and thorough."\n'
            f'}}'
        )

        result = self.call_llm_json(prompt)
        if result and "response" in result:
            result.setdefault("confidence", 0.85)
            result.setdefault("category", category or "general")
            return result
        return None

    def _categorize_issue(self, message: str) -> Optional[str]:
        message_lower = message.lower()
        for category, kb in self.knowledge_base.items():
            for symptom in kb["symptoms"]:
                if symptom in message_lower:
                    return category
        return None

    def _format_response(self, category: str, kb: Dict, user_message: str) -> str:
        category_names = {
            "vpn": "VPN Connection", "email": "Email",
            "printer": "Printer", "performance": "System Performance",
            "account": "Account Access", "software": "Software",
        }
        response = f"## 🔧 {category_names.get(category, category.title())} Troubleshooting\n\n"
        response += f"I've identified this as a **{category_names.get(category, category)}** issue. "
        response += "Here's a step-by-step guide to resolve it:\n\n"

        response += "### Diagnostic Checks\n"
        for diag in kb["diagnosis"][:3]:
            response += f"- {diag}\n"

        response += "\n### Suggested Solutions\n"
        for fix in kb["solutions"]:
            response += f"**Step {fix['step']}:** {fix['action']}\n"
            response += f"   → {fix['detail']}\n\n"

        response += f"### Need More Help?\n{kb['escalation']}\n"
        response += "\n---\n*A support ticket has been created for tracking.*"
        return response
