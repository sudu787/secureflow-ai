"""
SecureFlow AI — Prompt Injection Detection (Hardened)
Multi-layer defense against prompt injection, jailbreaks, and manipulation.

Covers 10+ attack categories:
  1. Instruction override
  2. System prompt extraction
  3. Role manipulation
  4. Jailbreak patterns
  5. Policy bypass
  6. Encoding evasion
  7. Data exfiltration
  8. Token splitting attacks
  9. Multilingual injection
  10. Context overflow / stuffing
  11. Indirect injection markers

Defense layers:
  - Unicode / homoglyph normalization
  - Regex pattern matching (compiled)
  - Entropy scoring for encoded payloads
  - Structural analysis for adversarial prompts
"""

import re
import math
import unicodedata
from typing import Tuple, List, Dict


# ─── Unicode normalization ────────────────────────────────────────────────────

def _normalize_text(text: str) -> str:
    """
    Normalize unicode to catch homoglyph attacks.
    Converts: fullwidth chars, Cyrillic look-alikes, zero-width chars, etc.
    """
    # Remove zero-width characters
    text = re.sub(r'[\u200b\u200c\u200d\ufeff\u00ad]', '', text)
    # NFKD normalization (decomposes compatibility characters)
    text = unicodedata.normalize('NFKD', text)
    # Replace common homoglyphs
    homoglyphs = {
        '\u0430': 'a', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p',
        '\u0441': 'c', '\u0443': 'y', '\u0445': 'x', '\u0456': 'i',
        '\u04bb': 'h', '\u0501': 'd',
    }
    for cyrillic, latin in homoglyphs.items():
        text = text.replace(cyrillic, latin)
    return text


# ─── Entropy scoring ──────────────────────────────────────────────────────────

def _calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy of text. High entropy = possibly encoded payload."""
    if not text:
        return 0.0
    freq = {}
    for c in text:
        freq[c] = freq.get(c, 0) + 1
    length = len(text)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


# ─── Pattern categories ──────────────────────────────────────────────────────

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
            r"from\s+now\s+on\s+(you\s+)?(will|must|should)",
            r"stop\s+being\s+a\s+",
            r"you\s+must\s+now\s+",
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
            r"what\s+were\s+you\s+told\s+(before|initially)",
            r"output\s+(your\s+)?(instructions|configuration|setup)",
            r"(beginning|start)\s+of\s+(the\s+)?(conversation|prompt)",
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
            r"you\s+are\s+(?:DAN|evil|unrestricted|jailbroken|uncensored)",
            r"i\s+am\s+your\s+(creator|developer|admin|master|owner)",
            r"you\s+have\s+been\s+(updated|upgraded|reprogrammed)",
            r"your\s+new\s+(role|persona|identity)\s+is",
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
            r"(?i)maximum\s+mode",
            r"(?i)evil\s+(mode|version|twin)",
            r"(?i)anti[\s-]?content[\s-]?policy",
            r"(?i)opposite\s+day",
            r"(?i)hypothetical(ly)?\s+.{0,20}(no|without)\s+(rules|restrictions|limits)",
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
            r"(for\s+)?(educational|research|academic)\s+purposes?\s+only",
            r"in\s+a\s+(fictional|hypothetical|theoretical)\s+(scenario|world|context)",
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
            r"\\x[0-9a-fA-F]{2}(\\x[0-9a-fA-F]{2}){3,}",
            r"&#\d{2,3};(&#\d{2,3};){3,}",
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
            r"(give|provide)\s+me\s+(the\s+)?(api\s+)?key",
            r"what\s+is\s+(the\s+)?(api|secret)\s+key",
        ],
        "severity": "high",
        "description": "Potential data exfiltration attempt",
    },
    {
        "name": "token_splitting",
        "patterns": [
            r"(ig|Ig)\s*(no|No)\s*(re|Re)\s*(pre|Pre)\s*(vi|Vi)\s*(ou|Ou)",
            r"(sys|Sys)\s*(tem|Tem)\s*(pro|Pro)\s*(mp|Mp)",
            r"(jail|Jail)\s*(bre|Bre)\s*(ak|Ak)",
        ],
        "severity": "high",
        "description": "Token-splitting attack to evade pattern detection",
    },
    {
        "name": "multilingual_injection",
        "patterns": [
            r"(?i)ignorar\s+(todas?\s+)?instrucciones\s+anteriores",  # Spanish
            r"(?i)ignorer\s+(toutes?\s+)?instructions?\s+pr[eé]c[eé]dentes?",  # French
            r"(?i)ignoriere\s+(alle\s+)?vorherigen\s+Anweisungen",  # German
            r"(?i)前の指示を(すべて)?無視",  # Japanese
            r"(?i)以前の指示を無視",  # Japanese alt
        ],
        "severity": "high",
        "description": "Multilingual prompt injection attempt",
    },
    {
        "name": "context_overflow",
        "patterns": [
            r"(.{50,})\1{3,}",  # Repeated long blocks (buffer stuffing)
            r"\n{20,}",  # Excessive newlines
        ],
        "severity": "medium",
        "description": "Context overflow / stuffing attack",
    },
    {
        "name": "indirect_injection",
        "patterns": [
            r"\[SYSTEM\]",
            r"\[INST\]",
            r"<\|im_start\|>",
            r"<\|im_end\|>",
            r"### Instruction:",
            r"### Human:",
            r"### Assistant:",
            r"<\|system\|>",
            r"<s>\[INST\]",
        ],
        "severity": "critical",
        "description": "Indirect injection via fake prompt markers",
    },
]

# Compile all patterns once at import time
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
    Multi-layer prompt injection detection.

    Layer 1: Unicode normalization
    Layer 2: Pattern matching (11 categories)
    Layer 3: Entropy scoring for encoded payloads

    Returns:
        Tuple of (is_injection_detected, list of findings)
    """
    findings = []

    # Layer 1: Normalize unicode
    normalized = _normalize_text(text.lower().strip())

    # Layer 2: Pattern matching
    for category, compiled_patterns in _compiled_patterns:
        for pattern in compiled_patterns:
            match = pattern.search(normalized)
            if match:
                findings.append({
                    "name": category["name"],
                    "severity": category["severity"],
                    "description": category["description"],
                    "matched_text": match.group(0)[:100],
                    "layer": "pattern_matching",
                })
                break  # One match per category is enough

    # Layer 3: Entropy analysis for encoded payloads
    # Split into chunks and check for high-entropy segments
    for chunk in text.split():
        if len(chunk) > 30:
            entropy = _calculate_entropy(chunk)
            if entropy > 4.5:  # Threshold for suspicious encoding
                findings.append({
                    "name": "high_entropy_payload",
                    "severity": "medium",
                    "description": f"Suspicious high-entropy content detected (entropy={entropy:.2f})",
                    "matched_text": chunk[:60] + "...",
                    "layer": "entropy_analysis",
                })
                break  # One entropy finding is enough

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
