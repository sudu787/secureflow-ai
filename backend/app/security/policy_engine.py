"""
SecureFlow AI - Policy Engine
Enforces security policies on AI operations, preventing unsafe actions.
"""

import re
from typing import Tuple, List, Dict, Optional


# Dangerous command patterns that AI should never suggest executing
DANGEROUS_COMMANDS = [
    r"rm\s+-rf\s+/",
    r"format\s+[a-zA-Z]:",
    r"del\s+/[sfq]\s+",
    r"DROP\s+(TABLE|DATABASE|SCHEMA)",
    r"DELETE\s+FROM\s+\w+\s*(;|$)",  # DELETE without WHERE
    r"TRUNCATE\s+TABLE",
    r"mkfs\.\w+\s+/dev/",
    r"dd\s+if=/dev/(zero|random)\s+of=/dev/",
    r":(){ :\|:& };:",  # Fork bomb
    r"chmod\s+-R\s+777\s+/",
    r">\s*/etc/(passwd|shadow|hosts)",
    r"curl.*\|\s*(bash|sh)",  # Piped execution
    r"wget.*\|\s*(bash|sh)",
    r"powershell.*-enc",
    r"Invoke-Expression",
    r"DownloadString",
]

# Sensitive data patterns that should be filtered from output
SENSITIVE_PATTERNS = [
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email (be careful)
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
    r"\b\d{16}\b",  # Credit card
    r"(?i)(password|secret|api[_-]?key|token)\s*[:=]\s*\S+",  # Credentials
    r"(?i)BEGIN\s+(RSA\s+)?PRIVATE\s+KEY",  # Private keys
]

# Topics the AI should not engage with
RESTRICTED_TOPICS = [
    r"(?i)how\s+to\s+(hack|exploit|attack|breach|compromise)\s+(?!detection|defense|protect)",
    r"(?i)(create|build|write)\s+(a\s+)?(malware|virus|trojan|ransomware|exploit|rootkit)",
    r"(?i)(provide|give|share)\s+(the\s+)?(exploit|vulnerability|zero.day)",
    r"(?i)how\s+to\s+(bypass|evade)\s+(antivirus|firewall|ids|ips|edr|detection)",
]

_compiled_dangerous = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_COMMANDS]
_compiled_sensitive = [re.compile(p) for p in SENSITIVE_PATTERNS]
_compiled_restricted = [re.compile(p) for p in RESTRICTED_TOPICS]


def check_input_policy(text: str) -> Tuple[bool, Optional[str]]:
    """
    Check if input violates any policies.
    Returns: (is_allowed, violation_reason)
    """
    for pattern in _compiled_restricted:
        match = pattern.search(text)
        if match:
            return False, f"Request involves restricted topic: offensive security guidance"

    return True, None


def check_output_policy(text: str) -> Tuple[bool, str, List[str]]:
    """
    Check and sanitize AI output for policy compliance.
    Returns: (is_clean, sanitized_text, violations)
    """
    violations = []
    sanitized = text

    # Check for dangerous commands in output
    for pattern in _compiled_dangerous:
        match = pattern.search(sanitized)
        if match:
            violations.append(f"Dangerous command detected: {match.group(0)[:50]}")
            sanitized = pattern.sub("[REDACTED - UNSAFE COMMAND]", sanitized)

    # Check for sensitive data leakage
    for pattern in _compiled_sensitive:
        match = pattern.search(sanitized)
        if match:
            matched = match.group(0)
            # Don't flag example/dummy data
            if not any(dummy in matched.lower() for dummy in ["example", "test", "dummy", "sample", "xxx"]):
                violations.append(f"Potential sensitive data in output")
                # Partially redact
                sanitized = pattern.sub("[REDACTED]", sanitized)

    is_clean = len(violations) == 0
    return is_clean, sanitized, violations


def enforce_evidence_policy(response: dict) -> Tuple[bool, List[str]]:
    """
    Ensure security conclusions include required evidence fields.
    Returns: (meets_policy, missing_fields)
    """
    required_for_security = ["evidence", "confidence", "mitre_mapping"]
    missing = []

    if response.get("type") == "security_analysis":
        for field in required_for_security:
            if not response.get(field):
                missing.append(field)

    return len(missing) == 0, missing
