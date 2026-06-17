"""
SecureFlow AI - Output Validator
Final validation layer before AI responses reach the user.
Ensures evidence-based reasoning, no hallucinated facts, and policy compliance.
"""

from typing import Tuple, Dict, Any, List, Optional
from app.security.policy_engine import check_output_policy


def validate_ai_output(
    response_text: str,
    response_type: str = "general",
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str, List[str]]:
    """
    Validate AI output before delivering to user.

    Args:
        response_text: The AI-generated response text
        response_type: Type of response (general, security_analysis, remediation, it_support)
        context: Additional context about the request

    Returns:
        Tuple of (is_valid, processed_text, warnings)
    """
    warnings = []

    # Step 1: Policy compliance check
    is_clean, sanitized, policy_violations = check_output_policy(response_text)
    if not is_clean:
        warnings.extend(policy_violations)

    # Step 2: Check for unsupported claims in security analysis
    if response_type == "security_analysis":
        unsupported_markers = [
            "definitely",
            "guaranteed",
            "100%",
            "absolutely certain",
            "without a doubt",
            "it is certain that",
        ]
        for marker in unsupported_markers:
            if marker.lower() in sanitized.lower():
                warnings.append(f"Unsupported certainty claim detected: '{marker}'")
                sanitized = sanitized.replace(marker, "with high confidence")

    # Step 3: Ensure response doesn't claim capabilities it doesn't have
    false_capability_markers = [
        "I have blocked",
        "I have quarantined",
        "I have disabled",
        "I have deleted",
        "I have executed",
        "I have deployed",
    ]
    for marker in false_capability_markers:
        if marker.lower() in sanitized.lower():
            warnings.append(f"False capability claim: '{marker}'")
            sanitized = sanitized.replace(
                marker,
                marker.replace("have", "recommend to"),
            )

    # Step 4: Add evidence disclaimer if needed
    if response_type == "security_analysis" and "evidence" not in sanitized.lower():
        sanitized += "\n\n*Note: Always verify findings against your actual infrastructure before taking action.*"

    is_valid = len(warnings) == 0
    return is_valid, sanitized, warnings
