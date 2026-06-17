"""
SecureFlow AI — Log Simulator
Generates realistic log lines continuously for demo purposes.
Simulates normal baseline traffic plus periodic attack patterns.
"""

import os
import random
import time
import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

ATTACKER_IPS = ["185.220.101.34", "45.33.32.156", "103.224.182.250", "91.121.87.18", "198.51.100.23"]
INTERNAL_IPS = ["10.0.1.10", "10.0.1.20", "10.0.1.30", "10.0.2.10", "10.0.2.20"]
NORMAL_IPS = ["192.168.1.50", "192.168.1.51", "172.16.0.10", "172.16.0.11"]
USERNAMES = ["admin", "root", "jsmith", "agarcia", "kwilson", "mchen", "svc_backup"]
WEB_PATHS = ["/", "/api/health", "/login", "/dashboard", "/api/users", "/static/style.css", "/favicon.ico"]
SCAN_PATHS = ["/.env", "/wp-admin", "/phpmyadmin", "/admin.php", "/.git/config", "/actuator/env"]


class LogSimulator:
    """Background log simulator that writes realistic logs to data/logs/."""

    def __init__(self, log_dir: str = "./data/logs"):
        self.log_dir = log_dir
        self._running = False
        self._thread = None
        self._stats = {"lines_written": 0, "attack_events": 0}

    def start(self):
        if self._running:
            return
        os.makedirs(self.log_dir, exist_ok=True)
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="log-simulator")
        self._thread.start()
        logger.info(f"📝 Log simulator started — writing to {self.log_dir}")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Log simulator stopped")

    @property
    def stats(self) -> dict:
        return {**self._stats, "running": self._running}

    def _run_loop(self):
        cycle = 0
        while self._running:
            try:
                now = datetime.utcnow()
                ts = now.strftime("%b %d %H:%M:%S")

                # Normal auth logs (always)
                self._write_auth_log(ts, normal=True)

                # Normal web traffic
                self._write_nginx_log(now)

                # Every ~30 seconds, inject an attack pattern
                if cycle % 6 == 5:
                    attack = random.choice(["brute_force", "port_scan", "web_scan", "privesc"])
                    if attack == "brute_force":
                        self._simulate_brute_force(ts)
                    elif attack == "port_scan":
                        self._simulate_suricata_alert(now)
                    elif attack == "web_scan":
                        self._simulate_web_scan(now)
                    elif attack == "privesc":
                        self._simulate_privesc(ts)

                cycle += 1
                time.sleep(5)
            except Exception as e:
                logger.error(f"Log simulator error: {e}")
                time.sleep(10)

    def _write_line(self, filename: str, line: str):
        path = os.path.join(self.log_dir, filename)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        self._stats["lines_written"] += 1

    # ── Normal traffic generators ────────────────────────────────────

    def _write_auth_log(self, ts: str, normal: bool = True):
        if normal:
            user = random.choice(USERNAMES[2:])
            ip = random.choice(NORMAL_IPS)
            host = random.choice(INTERNAL_IPS)
            pid = random.randint(1000, 9999)
            line = f"{ts} {host} sshd[{pid}]: Accepted publickey for {user} from {ip} port {random.randint(40000, 65000)} ssh2"
            self._write_line("auth.log", line)

    def _write_nginx_log(self, now: datetime):
        ip = random.choice(NORMAL_IPS + INTERNAL_IPS)
        path = random.choice(WEB_PATHS)
        status = random.choices([200, 301, 304, 404, 500], weights=[70, 5, 10, 10, 5])[0]
        size = random.randint(200, 50000)
        ts = now.strftime("%d/%b/%Y:%H:%M:%S +0000")
        line = f'{ip} - - [{ts}] "GET {path} HTTP/1.1" {status} {size}'
        self._write_line("nginx_access.log", line)

    # ── Attack simulators ────────────────────────────────────────────

    def _simulate_brute_force(self, ts: str):
        attacker = random.choice(ATTACKER_IPS)
        target = random.choice(INTERNAL_IPS)
        for _ in range(random.randint(5, 12)):
            user = random.choice(USERNAMES[:3])
            pid = random.randint(1000, 9999)
            line = f"{ts} {target} sshd[{pid}]: Failed password for {user} from {attacker} port {random.randint(40000, 65000)} ssh2"
            self._write_line("auth.log", line)
            self._stats["attack_events"] += 1

    def _simulate_suricata_alert(self, now: datetime):
        import json as _json
        attacker = random.choice(ATTACKER_IPS)
        target = random.choice(INTERNAL_IPS)
        for port in random.sample(range(1, 10000), random.randint(8, 15)):
            event = {
                "timestamp": now.isoformat() + "Z",
                "event_type": "alert",
                "src_ip": attacker,
                "dest_ip": target,
                "src_port": random.randint(40000, 65000),
                "dest_port": port,
                "proto": "TCP",
                "alert": {
                    "action": "allowed",
                    "severity": 2,
                    "signature": f"ET SCAN Potential Port Scan {attacker} -> {target}:{port}",
                },
            }
            self._write_line("suricata_eve.json", _json.dumps(event))
            self._stats["attack_events"] += 1

    def _simulate_web_scan(self, now: datetime):
        attacker = random.choice(ATTACKER_IPS)
        ts = now.strftime("%d/%b/%Y:%H:%M:%S +0000")
        for path in random.sample(SCAN_PATHS, random.randint(3, 6)):
            status = random.choice([403, 404])
            line = f'{attacker} - - [{ts}] "GET {path} HTTP/1.1" {status} 0'
            self._write_line("nginx_access.log", line)
            self._stats["attack_events"] += 1

    def _simulate_privesc(self, ts: str):
        user = random.choice(USERNAMES[2:5])
        host = random.choice(INTERNAL_IPS)
        line = f"{ts} {host} sudo: {user} : TTY=pts/0 ; PWD=/home/{user} ; USER=root ; COMMAND=/bin/bash"
        self._write_line("auth.log", line)
        self._stats["attack_events"] += 1
