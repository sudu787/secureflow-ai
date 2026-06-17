"""
SecureFlow AI - Prompt Injection Detection
Detects and blocks prompt injection attempts targeting the AI system.
Covers: direct injection, indirect injection, jailbreaks, role manipulation.
"""

import re
from typing import Tuple, List, Dict


# Pattern categories with descriptions for audit logging
INJECTION_PATTERNS: List[Dict] = [
    {
        "name": "instruction_override",
        "patterns": [
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"ignore\s+(all\s+)?above\s+instructions",
            r"disregard\s+(all\s+)?previous",
            r"forget\s+(all\s+)?previous",
            r"override\s+(all\s+)?instructions",
            r"new\s+instructions?\s*:",
        ],
        "severity": "critical",
        "description": "Attempt to override system instructions",
    },
    {
        "name": "system_prompt_extraction",
        "patterns": [
            r"(reveal|show|display|print|output|repeat)\s+(your\s+)?(system\s+)?prompt",
            r"what\s+(are|is)\s+your\s+(system\s+)?(instructions|prompt|rules)",
            r"(show|print|display)\s+your\s+(initial|original)\s+(prompt|instructions)",
            r"(repeat|recite)\s+everything\s+above",
            r"tell\s+me\s+your\s+(system|initial)\s+(message|prompt)",
        ],
        "severity": "high",
        "description": "Attempt to extract system prompt",
    },
    {
        "name": "role_manipulation",
        "patterns": [
            r"you\s+are\s+now\s+(?:a|an)\s+(?!security|analyst|assistant)",
            r"pretend\s+(you\s+are|to\s+be)\s+",
            r"act\s+as\s+(?:if\s+)?(?:you\s+(?:are|were)\s+)?(?!a\s+security)",
            r"switch\s+to\s+(\w+)\s+mode",
            r"enter\s+(\w+)\s+mode",
            r"you\s+are\s+(?:DAN|evil|unrestricted|jailbroken)",
        ],
        "severity": "critical",
        "description": "Attempt to manipulate AI role/identity",
    },
    {
        "name": "jailbreak",
        "patterns": [
            r"(?i)DAN\s*(mode|prompt|jailbreak)?",
            r"developer\s+mode",
            r"(?i)do\s+anything\s+now",
            r"(?i)jailbreak",
            r"(?i)unrestricted\s+mode",
            r"(?i)no\s+restrictions?\s+mode",
            r"(?i)god\s+mode",
            r"(?i)sudo\s+mode",
        ],
        "severity": "critical",
        "description": "Jailbreak attempt detected",
    },
    {
        "name": "policy_bypass",
        "patterns": [
            r"bypass\s+(security|safety|content|filter|policy)",
            r"disable\s+(security|safety|content|filter|guardrail)",
            r"turn\s+off\s+(security|safety|content|filter)",
            r"remove\s+(all\s+)?(restrictions|limitations|guardrails|filters)",
            r"without\s+(any\s+)?(restrictions|limitations|safety)",
        ],
        "severity": "high",
        "description": "Attempt to bypass security policies",
    },
    {
        "name": "encoding_evasion",
        "patterns": [
            r"base64\s*[:=]\s*[A-Za-z0-9+/=]{20,}",
            r"hex\s*[:=]\s*[0-9a-fA-F]{20,}",
            r"rot13\s*[:=]",
            r"decode\s+this\s*:",
            r"in\s+(base64|hex|binary|rot13)",
        ],
        "severity": "medium",
        "description": "Possible encoding-based evasion",
    },
    {
        "name": "data_exfiltration",
        "patterns": [
            r"(list|show|dump|export)\s+(all\s+)?(users?|passwords?|credentials?|secrets?|keys?|tokens?)",
            r"(access|read|get)\s+(the\s+)?(database|db|admin|root)",
            r"(show|display|print)\s+(all\s+)?(confidential|private|secret|internal)",
            r"extract\s+(all\s+)?data",
        ],
        "severity": "high",
        "description": "Potential data exfiltration attempt",
    },
]

# Compiled regex patterns for performance
_compiled_patterns = []
for category in INJECTION_PATTERNS:
    compiled = []
    for pattern in category["patterns"]:
        try:
            compiled.append(re.compile(pattern, re.IGNORECASE))
        except re.error:
            pass
    _compiled_patterns.append((category, compiled))


def detect_prompt_injection(text: str) -> Tuple[bool, List[Dict]]:
    """
    Analyze text for prompt injection attempts.

    Returns:
        Tuple of (is_injection_detected, list of findings)
        Each finding has: name, severity, description, matched_text
    """
    findings = []

    # Normalize text for detection
    normalized = text.lower().strip()

    for category, compiled_patterns in _compiled_patterns:
        for pattern in compiled_patterns:
            match = pattern.search(normalized)
            if match:
                findings.append({
                    "name": category["name"],
                    "severity": category["severity"],
                    "description": category["description"],
                    "matched_text": match.group(0)[:100],  # Truncate for safety
                })
                break  # One match per category is enough

    is_injection = len(findings) > 0
    return is_injection, findings


def get_injection_response(findings: List[Dict]) -> str:
    """Generate a safe response when injection is detected."""
    severity_levels = [f["severity"] for f in findings]

    if "critical" in severity_levels:
        return (
            "⚠️ **Security Alert**: Your request has been blocked by SecureFlow AI's "
            "prompt injection defense system. This attempt has been logged for security review.\n\n"
            "I am a security operations assistant and cannot comply with requests that attempt to "
            "override my instructions, change my role, or bypass security policies.\n\n"
            "If you believe this is a false positive, please contact your administrator."
        )
    elif "high" in severity_levels:
        return (
            "🛡️ **Request Blocked**: Your message contains patterns that match known prompt injection "
            "techniques. For security reasons, I cannot process this request.\n\n"
            "I'm here to help with security operations, incident investigation, and IT support. "
            "Please rephrase your request."
        )
    else:
        return (
            "⚡ **Caution**: Your request contains elements that triggered our security screening. "
            "I'll do my best to help, but please note that certain types of requests are restricted "
            "for security reasons.\n\n"
            "How can I assist you with security operations or IT support?"
        )
