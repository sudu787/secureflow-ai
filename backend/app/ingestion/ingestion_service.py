"""
SecureFlow AI — Ingestion Service
Background service that:
  1. Runs the log simulator (generates realistic logs)
  2. Watches log files for new lines (tail -f style)
  3. Parses and normalizes raw logs into Events
  4. Feeds events through the Detection Engine
  5. Auto-creates Alerts from detection results
"""

import os
import time
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class IngestionService:
    """Background log ingestion and processing pipeline."""

    def __init__(self):
        from app.config import settings
        self.log_dir = settings.LOG_WATCH_DIR
        self.interval = settings.INGESTION_INTERVAL_SECONDS
        self.enable_simulator = settings.ENABLE_LOG_SIMULATOR

        self._running = False
        self._thread = None
        self._simulator = None
        self._file_positions: Dict[str, int] = {}  # Track read position per file
        self._stats = {
            "events_ingested": 0,
            "alerts_created": 0,
            "errors": 0,
            "last_ingestion": None,
            "started_at": None,
        }

    def start(self):
        """Start the ingestion pipeline."""
        if self._running:
            return

        os.makedirs(self.log_dir, exist_ok=True)

        # Start log simulator if enabled
        if self.enable_simulator:
            from app.ingestion.log_simulator import LogSimulator
            self._simulator = LogSimulator(self.log_dir)
            self._simulator.start()

        self._running = True
        self._stats["started_at"] = datetime.utcnow().isoformat()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="ingestion-service")
        self._thread.start()
        logger.info(f"🚀 Ingestion service started — watching {self.log_dir} every {self.interval}s")

    def stop(self):
        """Stop the ingestion pipeline."""
        self._running = False
        if self._simulator:
            self._simulator.stop()
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("Ingestion service stopped")

    @property
    def status(self) -> dict:
        sim_stats = self._simulator.stats if self._simulator else {"running": False}
        return {
            "running": self._running,
            "log_dir": self.log_dir,
            "interval_seconds": self.interval,
            "simulator": sim_stats,
            **self._stats,
        }

    def _run_loop(self):
        """Main ingestion loop — read new log lines, parse, detect, alert."""
        # Wait briefly for app to fully start
        time.sleep(3)

        while self._running:
            try:
                new_events = self._collect_new_lines()
                if new_events:
                    self._process_events(new_events)
                    self._stats["last_ingestion"] = datetime.utcnow().isoformat()
            except Exception as e:
                logger.error(f"Ingestion error: {e}")
                self._stats["errors"] += 1

            time.sleep(self.interval)

    def _collect_new_lines(self) -> List[Dict]:
        """Read new lines from all log files in the watch directory."""
        from app.ingestion.log_parser import LogParser

        all_events = []
        if not os.path.exists(self.log_dir):
            return all_events

        for filename in os.listdir(self.log_dir):
            filepath = os.path.join(self.log_dir, filename)
            if not os.path.isfile(filepath):
                continue

            # Get the last read position
            last_pos = self._file_positions.get(filepath, 0)

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(last_pos)
                    new_lines = f.readlines()
                    self._file_positions[filepath] = f.tell()

                # Parse each new line
                source_hint = None
                if "auth" in filename:
                    source_hint = "auth.log"
                elif "nginx" in filename:
                    source_hint = "nginx"
                elif "suricata" in filename:
                    source_hint = "suricata"

                for line in new_lines:
                    line = line.strip()
                    if not line:
                        continue
                    event = LogParser.parse(line, source_hint=source_hint)
                    if event:
                        all_events.append(event)

            except Exception as e:
                logger.warning(f"Error reading {filepath}: {e}")

        return all_events

    def _process_events(self, events: List[Dict]):
        """Store events and run detection pipeline."""
        from app.database import SessionLocal
        from app.models.event import Event as EventModel
        from app.models.alert import Alert as AlertModel
        from app.detection.rule_engine import run_all_rules
        from app.detection.behavioral import run_behavioral_detection

        db = SessionLocal()
        try:
            # Store events in database
            for event_data in events:
                event = EventModel(
                    source_type=event_data.get("source_type", "unknown"),
                    source_name=event_data.get("source_name", "unknown"),
                    raw_log=event_data.get("raw_log", ""),
                    normalized_data=event_data.get("normalized_data"),
                    severity=event_data.get("severity", "info"),
                    confidence=event_data.get("confidence", 0.5),
                    mitre_technique=event_data.get("mitre_technique"),
                    mitre_tactic=event_data.get("mitre_tactic"),
                    source_ip=event_data.get("source_ip"),
                    dest_ip=event_data.get("dest_ip"),
                    username=event_data.get("username"),
                    action=event_data.get("action"),
                    timestamp=event_data.get("timestamp", datetime.utcnow()),
                )
                db.add(event)

            db.commit()
            self._stats["events_ingested"] += len(events)

            # Run detection rules
            rule_alerts = run_all_rules(events, db)
            behavioral_alerts = run_behavioral_detection(events)
            all_alerts = rule_alerts + behavioral_alerts

            # Store alerts
            for alert_data in all_alerts:
                alert = AlertModel(
                    alert_type=alert_data.get("alert_type", "unknown"),
                    severity=alert_data.get("severity", "medium"),
                    confidence=alert_data.get("confidence", 0.5),
                    title=alert_data.get("title", "Detection Alert"),
                    description=alert_data.get("description"),
                    affected_assets=alert_data.get("affected_assets"),
                    evidence=alert_data.get("evidence"),
                    mitre_id=alert_data.get("mitre_id"),
                    mitre_tactic=alert_data.get("mitre_tactic"),
                    mitre_technique_name=alert_data.get("mitre_technique_name"),
                    source_ip=alert_data.get("source_ip"),
                    dest_ip=alert_data.get("dest_ip"),
                    status="open",
                    priority="P3",
                )
                db.add(alert)
                self._stats["alerts_created"] += 1

            if all_alerts:
                db.commit()
                logger.info(
                    f"📊 Ingested {len(events)} events, created {len(all_alerts)} alerts"
                )

        except Exception as e:
            db.rollback()
            logger.error(f"Event processing error: {e}")
            self._stats["errors"] += 1
        finally:
            db.close()


# Singleton
_service_instance = None


def get_ingestion_service() -> IngestionService:
    global _service_instance
    if _service_instance is None:
        _service_instance = IngestionService()
    return _service_instance
