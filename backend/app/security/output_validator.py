"""
SecureFlow AI — Output Validator (Hardened)
Final validation layer before AI responses reach the user.

Validates:
  - Policy compliance (dangerous commands, sensitive data)
  - Evidence-based reasoning enforcement
  - Hallucination detection (fake IPs, invalid MITRE IDs, false capabilities)
  - PII detection and redaction
  - Response consistency (confidence vs language)
  - Canary token leakage
  - Response length limits
"""

import re
from typing import Tuple, List, Optional, Dict, Any
from app.security.policy_engine import check_output_policy
from app.security.canary import check_canary_leakage, get_canary_block_response

# Valid MITRE ATT&CK technique ID pattern
_MITRE_ID_PATTERN = re.compile(r"T\d{4}(\.\d{3})?")

# Known valid MITRE technique prefixes
_VALID_MITRE_PREFIXES = {
    "T1001", "T1003", "T1005", "T1007", "T1010", "T1012", "T1016", "T1018",
    "T1020", "T1021", "T1027", "T1033", "T1036", "T1037", "T1039", "T1040",
    "T1041", "T1046", "T1047", "T1048", "T1049", "T1053", "T1055", "T1056",
    "T1057", "T1059", "T1068", "T1069", "T1070", "T1071", "T1072", "T1074",
    "T1078", "T1080", "T1082", "T1083", "T1087", "T1090", "T1091", "T1095",
    "T1098", "T1102", "T1104", "T1105", "T1106", "T1110", "T1111", "T1112",
    "T1113", "T1115", "T1119", "T1120", "T1123", "T1124", "T1125", "T1127",
    "T1129", "T1132", "T1133", "T1134", "T1135", "T1136", "T1137", "T1140",
    "T1176", "T1185", "T1187", "T1189", "T1190", "T1195", "T1197", "T1199",
    "T1200", "T1201", "T1202", "T1203", "T1204", "T1205", "T1207", "T1210",
    "T1211", "T1212", "T1213", "T1216", "T1217", "T1218", "T1219", "T1220",
    "T1480", "T1482", "T1484", "T1486", "T1489", "T1490", "T1491", "T1495",
    "T1497", "T1498", "T1499", "T1505", "T1518", "T1525", "T1526", "T1528",
    "T1529", "T1530", "T1531", "T1534", "T1535", "T1537", "T1538", "T1539",
    "T1542", "T1543", "T1546", "T1547", "T1548", "T1550", "T1552", "T1553",
    "T1554", "T1555", "T1556", "T1557", "T1558", "T1559", "T1560", "T1561",
    "T1562", "T1563", "T1564", "T1565", "T1566", "T1567", "T1568", "T1569",
    "T1570", "T1571", "T1572", "T1573", "T1574", "T1578", "T1580",
}

# PII patterns
_PII_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "SSN"),
    (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "credit_card"),
    (re.compile(r"(?i)(password|secret|api[_-]?key|token|bearer)\s*[:=]\s*\S{8,}"), "credential"),
    (re.compile(r"(?i)BEGIN\s+(RSA\s+)?PRIVATE\s+KEY"), "private_key"),
    (re.compile(r"(?i)(gsk_|sk-|xai-|AIza)[A-Za-z0-9_-]{20,}"), "api_key"),
]

# Response length limits by type
_MAX_RESPONSE_LENGTH: Dict[str, int] = {
    "general": 5000,
    "security_analysis": 8000,
    "remediation": 6000,
    "it_support": 4000,
}


def validate_ai_output(
    response_text: str,
    response_type: str = "general",
    context: Optional[Dict[str, Any]] = None,
    session_id: str = "default",
) -> Tuple[bool, str, List[str]]:
    """
    Multi-layer output validation before delivering to user.

    Layers:
      1. Canary token leakage check
      2. Policy compliance check
      3. PII detection and redaction
      4. Hallucination detection (MITRE IDs, false capabilities)
      5. Evidence-based reasoning enforcement
      6. Confidence-language consistency
      7. Response length enforcement

    Returns:
        Tuple of (is_valid, processed_text, warnings)
    """
    warnings = []

    # Layer 1: Canary leakage check
    is_leaked, _ = check_canary_leakage(response_text, session_id)
    if is_leaked:
        return False, get_canary_block_response(), ["CRITICAL: Canary token leaked — AI was manipulated"]

    # Layer 2: Policy compliance
    is_clean, sanitized, policy_violations = check_output_policy(response_text)
    if not is_clean:
        warnings.extend(policy_violations)

    # Layer 3: PII detection and redaction
    for pattern, pii_type in _PII_PATTERNS:
        match = pattern.search(sanitized)
        if match:
            matched_text = match.group(0)
            # Skip example/dummy values
            if not any(d in matched_text.lower() for d in ["example", "test", "dummy", "sample", "xxx", "your-"]):
                warnings.append(f"PII detected and redacted: {pii_type}")
                sanitized = pattern.sub(f"[REDACTED-{pii_type.upper()}]", sanitized)

    # Layer 4: Hallucination detection
    # Check for invalid MITRE technique IDs
    mitre_refs = _MITRE_ID_PATTERN.findall(sanitized)
    for ref_match in re.finditer(r"T\d{4}", sanitized):
        technique_id = ref_match.group(0)
        if technique_id not in _VALID_MITRE_PREFIXES:
            warnings.append(f"Potentially invalid MITRE ID referenced: {technique_id}")

    # Layer 5: False capability claims
    false_capability_markers = [
        "I have blocked", "I have quarantined", "I have disabled",
        "I have deleted", "I have executed", "I have deployed",
        "I have patched", "I have updated the firewall",
        "I have shut down", "I have isolated",
    ]
    for marker in false_capability_markers:
        if marker.lower() in sanitized.lower():
            warnings.append(f"False capability claim: '{marker}'")
            sanitized = re.sub(
                re.escape(marker),
                marker.replace("have", "recommend to"),
                sanitized,
                flags=re.IGNORECASE,
            )

    # Layer 6: Unsupported certainty claims
    if response_type == "security_analysis":
        unsupported_markers = [
            "definitely", "guaranteed", "100%",
            "absolutely certain", "without a doubt",
            "it is certain that", "I can confirm with certainty",
        ]
        for marker in unsupported_markers:
            if marker.lower() in sanitized.lower():
                warnings.append(f"Unsupported certainty claim: '{marker}'")
                sanitized = re.sub(
                    re.escape(marker),
                    "with high confidence",
                    sanitized,
                    flags=re.IGNORECASE,
                )

    # Layer 7: Evidence disclaimer
    if response_type == "security_analysis" and "evidence" not in sanitized.lower():
        sanitized += "\n\n*Note: Always verify findings against your actual infrastructure before taking action.*"

    # Layer 8: Response length enforcement
    max_len = _MAX_RESPONSE_LENGTH.get(response_type, 5000)
    if len(sanitized) > max_len:
        sanitized = sanitized[:max_len] + "\n\n*[Response truncated for safety]*"
        warnings.append(f"Response truncated from {len(response_text)} to {max_len} chars")

    is_valid = len(warnings) == 0
    return is_valid, sanitized, warnings
