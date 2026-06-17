"""
SecureFlow AI - Input Validation Layer
Sanitizes and validates all user inputs before they reach the AI system.
"""

import re
import html
from typing import Tuple, Optional
from app.config import settings


def validate_input(text: str) -> Tuple[bool, Optional[str], str]:
    """
    Validate and sanitize user input.

    Returns:
        Tuple of (is_valid, error_message, sanitized_text)
    """
    # Check for empty input
    if not text or not text.strip():
        return False, "Input cannot be empty.", ""

    # Check length limits
    if len(text) > settings.MAX_INPUT_LENGTH:
        return False, f"Input exceeds maximum length of {settings.MAX_INPUT_LENGTH} characters.", ""

    # Sanitize HTML to prevent XSS
    sanitized = html.escape(text)

    # Remove null bytes
    sanitized = sanitized.replace("\x00", "")

    # Remove excessive whitespace
    sanitized = re.sub(r"\s{10,}", " " * 5, sanitized)

    # Remove control characters (except newlines and tabs)
    sanitized = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", sanitized)

    return True, None, sanitized


def validate_ip_address(ip: str) -> bool:
    """Validate IPv4 address format."""
    pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    return bool(re.match(pattern, ip))


def validate_severity(severity: str) -> bool:
    """Validate severity level."""
    return severity.lower() in ["info", "low", "medium", "high", "critical"]


def validate_priority(priority: str) -> bool:
    """Validate priority level."""
    return priority.upper() in ["P1", "P2", "P3", "P4"]


def validate_status(status: str, status_type: str = "alert") -> bool:
    """Validate status value for different entity types."""
    valid_statuses = {
        "alert": ["open", "investigating", "resolved", "false_positive", "closed"],
        "incident": ["open", "investigating", "contained", "resolved", "closed"],
        "ticket": ["open", "in_progress", "escalated", "resolved", "closed"],
    }
    return status.lower() in valid_statuses.get(status_type, [])
