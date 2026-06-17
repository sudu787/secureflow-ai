"""
SecureFlow AI - Behavioral Detection
Anomaly-based detection using statistical baselines for frequency spikes,
unusual login patterns, and anomalous process execution.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict
import statistics


def detect_frequency_spike(
    events: List[Dict],
    field: str = "source_ip",
    window_minutes: int = 5,
    spike_multiplier: float = 3.0,
) -> List[Dict]:
    """
    Detect frequency spikes in events grouped by a field.
    A spike is when current window count exceeds historical average * multiplier.
    """
    alerts = []
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=window_minutes)

    # Group events by field value
    grouped = defaultdict(list)
    for event in events:
        grouped[event.get(field, "unknown")].append(event)

    for key, group_events in grouped.items():
        # Calculate recent vs baseline
        recent = [e for e in group_events
                  if isinstance(e.get("timestamp"), datetime) and e["timestamp"] >= window_start]
        older = [e for e in group_events
                 if isinstance(e.get("timestamp"), datetime) and e["timestamp"] < window_start]

        recent_count = len(recent)
        baseline_count = max(len(older), 1)

        if recent_count > baseline_count * spike_multiplier and recent_count >= 5:
            alerts.append({
                "alert_type": "frequency_spike",
                "severity": "medium",
                "confidence": min(0.95, 0.5 + (recent_count / baseline_count) * 0.1),
                "title": f"Frequency Spike Detected: {field}={key}",
                "description": (
                    f"Unusual spike in event frequency for {field}={key}. "
                    f"Recent window ({window_minutes}min): {recent_count} events, "
                    f"baseline: {baseline_count} events. "
                    f"Spike ratio: {recent_count/baseline_count:.1f}x"
                ),
                "affected_assets": [key],
                "evidence": {
                    "field": field,
                    "value": key,
                    "recent_count": recent_count,
                    "baseline_count": baseline_count,
                    "spike_ratio": round(recent_count / baseline_count, 2),
                    "window_minutes": window_minutes,
                },
                "mitre_id": "T1071",
                "mitre_tactic": "Discovery",
                "mitre_technique_name": "Application Layer Protocol",
                "source_ip": key if field == "source_ip" else None,
            })

    return alerts


def detect_unusual_login_time(
    events: List[Dict],
    business_hours: tuple = (8, 18),  # 8 AM to 6 PM
) -> List[Dict]:
    """Detect logins outside business hours."""
    alerts = []
    for event in events:
        if event.get("action") in ["login_success", "login_attempt"]:
            timestamp = event.get("timestamp")
            if isinstance(timestamp, datetime):
                hour = timestamp.hour
                if hour < business_hours[0] or hour >= business_hours[1]:
                    alerts.append({
                        "alert_type": "unusual_login_time",
                        "severity": "low",
                        "confidence": 0.65,
                        "title": f"Off-Hours Login: {event.get('username', 'unknown')} at {timestamp.strftime('%H:%M')}",
                        "description": (
                            f"User '{event.get('username', 'unknown')}' logged in at {timestamp.strftime('%H:%M')} "
                            f"from {event.get('source_ip', 'unknown IP')}, outside business hours "
                            f"({business_hours[0]}:00-{business_hours[1]}:00). "
                            f"This may be legitimate but warrants verification."
                        ),
                        "affected_assets": [event.get("username", "unknown")],
                        "evidence": {
                            "login_time": str(timestamp),
                            "username": event.get("username"),
                            "source_ip": event.get("source_ip"),
                            "business_hours": f"{business_hours[0]}:00-{business_hours[1]}:00",
                        },
                        "mitre_id": "T1078",
                        "mitre_tactic": "Defense Evasion",
                        "mitre_technique_name": "Valid Accounts",
                        "source_ip": event.get("source_ip"),
                    })
    return alerts


def run_behavioral_detection(events: List[Dict]) -> List[Dict]:
    """Run all behavioral detection methods."""
    all_alerts = []
    all_alerts.extend(detect_frequency_spike(events))
    all_alerts.extend(detect_unusual_login_time(events))
    return all_alerts
