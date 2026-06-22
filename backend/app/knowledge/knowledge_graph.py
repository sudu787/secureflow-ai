"""
SecureFlow AI — Security Knowledge Graph (FULL v2)
Central intelligence layer connecting ALL security entities.

Node Types (12):
  ip, user, device, asset, application, alert, incident,
  vulnerability/cve, threat_actor, malware, ioc,
  mitre_technique, mitre_tactic, security_control,
  compliance_control, software

Edges (50+):
  triggered, targets, targets_user, affects_device, maps_to,
  communicates_with, escalated_to, uses, exploits, implements,
  vulnerable_to, administers, accesses, involves, affects,
  attributed_to, logged_into, connected_to, hosts, runs,
  belongs_to, part_of, observed_in, mitigates, covers,
  maps_to_control, exploited_by, related_to, lateral_move_to,
  data_exfiltrated_via, spawned, contacted, hash_matches,
  domain_matches, ip_matches, patch_available_for,
  deployed_on, owned_by, member_of, reports_to, targets_industry,
  operates_from, funded_by, collaborated_with, signed_by,
  downloaded_from, persistence_on, c2_communicates_with,
  delivered_via, enabled_by, detects, prevents, requires
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("networkx not installed — knowledge graph disabled. pip install networkx")


# ── Entity colour map (used by visualization) ─────────────────────────────────

ENTITY_COLORS = {
    "ip":                 "#ef4444",   # red
    "user":               "#3b82f6",   # blue
    "device":             "#8b5cf6",   # purple
    "asset":              "#f59e0b",   # amber
    "application":        "#06b6d4",   # cyan
    "alert":              "#ef4444",   # red
    "incident":           "#b91c1c",   # dark-red
    "vulnerability":      "#f97316",   # orange
    "cve":                "#f97316",   # orange
    "threat_actor":       "#dc2626",   # crimson
    "malware":            "#7c3aed",   # violet
    "ioc":                "#ec4899",   # pink
    "mitre_technique":    "#10b981",   # emerald
    "mitre_tactic":       "#059669",   # dark-emerald
    "security_control":   "#0ea5e9",   # sky
    "compliance_control": "#64748b",   # slate
    "software":           "#84cc16",   # lime
}


class SecurityKnowledgeGraph:
    """
    Full-spectrum Security Knowledge Graph.

    Powers:
    - GraphRAG: graph context injected into every LLM agent call
    - Attack path reconstruction
    - Blast radius analysis
    - Risk propagation (cascade scoring)
    - Threat hunting queries (lateral movement, malicious IPs, etc.)
    - MITRE ATT&CK full integration (Tactic → Technique → Incident)
    - Vulnerability intelligence (CVE → Asset → Threat Actor)
    """

    def __init__(self):
        if HAS_NETWORKX:
            self._graph = nx.MultiDiGraph()   # MultiDiGraph allows multiple edges between same nodes
        else:
            self._graph = None
        self._stats = {"nodes": 0, "edges": 0, "queries": 0}

    @property
    def available(self) -> bool:
        return HAS_NETWORKX and self._graph is not None

    # ── Node Management ───────────────────────────────────────────────

    def add_entity(self, entity_id: str, entity_type: str, properties: Dict = None) -> str:
        """Add or update a node in the knowledge graph. Returns node_id."""
        if not self.available:
            return ""
        node_id = f"{entity_type}:{entity_id}"
        if node_id in self._graph:
            # Merge properties
            existing = self._graph.nodes[node_id].get("properties", {})
            if properties:
                existing.update(properties)
            self._graph.nodes[node_id]["properties"] = existing
        else:
            self._graph.add_node(
                node_id,
                entity_type=entity_type,
                entity_id=entity_id,
                properties=properties or {},
                created_at=datetime.utcnow().isoformat(),
                color=ENTITY_COLORS.get(entity_type, "#9ca3af"),
            )
        self._stats["nodes"] = self._graph.number_of_nodes()
        return node_id

    def add_relationship(
        self,
        source_id: str, source_type: str,
        target_id: str, target_type: str,
        relation: str,
        properties: Dict = None,
    ) -> None:
        """Add a directed edge between two entities (auto-creates nodes)."""
        if not self.available:
            return
        src = f"{source_type}:{source_id}"
        tgt = f"{target_type}:{target_id}"

        if src not in self._graph:
            self.add_entity(source_id, source_type)
        if tgt not in self._graph:
            self.add_entity(target_id, target_type)

        self._graph.add_edge(
            src, tgt,
            relation=relation,
            properties=properties or {},
            created_at=datetime.utcnow().isoformat(),
        )
        self._stats["edges"] = self._graph.number_of_edges()

    # ── Alert / Incident Ingestion ─────────────────────────────────────

    def ingest_alert(self, alert: Dict) -> None:
        """Ingest a security alert and wire all relevant graph relationships."""
        if not self.available:
            return

        alert_id   = str(alert.get("id", "unknown"))
        alert_type = alert.get("alert_type", "unknown")
        source_ip  = alert.get("source_ip")
        dest_ip    = alert.get("dest_ip")
        mitre_id   = alert.get("mitre_id")
        mitre_tac  = alert.get("mitre_tactic", "")
        severity   = alert.get("severity", "medium")
        evidence   = alert.get("evidence", {})
        confidence = alert.get("confidence", 0)

        # Alert node
        self.add_entity(alert_id, "alert", {
            "type": alert_type, "severity": severity,
            "title": alert.get("title", ""), "confidence": confidence,
        })

        # Source IP → triggered → Alert
        if source_ip:
            self.add_entity(source_ip, "ip", {"role": "source", "malicious": confidence > 0.7})
            self.add_relationship(source_ip, "ip", alert_id, "alert", "triggered")

        # Alert → targets → Dest IP
        if dest_ip:
            self.add_entity(dest_ip, "ip", {"role": "target"})
            self.add_relationship(alert_id, "alert", dest_ip, "ip", "targets")

        # IP ↔ IP communication
        if source_ip and dest_ip:
            self.add_relationship(source_ip, "ip", dest_ip, "ip", "communicates_with")

        # Alert → maps_to → MITRE Technique
        if mitre_id:
            self.add_entity(mitre_id, "mitre_technique", {
                "tactic": mitre_tac,
                "name": alert.get("mitre_technique_name", ""),
            })
            self.add_relationship(alert_id, "alert", mitre_id, "mitre_technique", "maps_to")

            # Technique → belongs_to → Tactic
            if mitre_tac:
                self.add_entity(mitre_tac, "mitre_tactic", {"name": mitre_tac})
                self.add_relationship(mitre_id, "mitre_technique", mitre_tac, "mitre_tactic", "belongs_to")

        # Users from evidence
        target_users = list(evidence.get("target_users", []))
        if evidence.get("username"):
            target_users.append(evidence["username"])
        for user in target_users:
            self.add_entity(user, "user", {"role": "targeted"})
            self.add_relationship(alert_id, "alert", user, "user", "targets_user")

        # Hostname / device
        hostname = evidence.get("hostname")
        if hostname:
            self.add_entity(hostname, "device", {"hostname": hostname})
            self.add_relationship(alert_id, "alert", hostname, "device", "affects_device")

        # IOCs from evidence
        for ioc_val in evidence.get("iocs", []):
            ioc_type = "hash" if len(ioc_val) in (32, 40, 64) else "ip" if "." in ioc_val else "domain"
            self.add_entity(ioc_val, "ioc", {"value": ioc_val, "ioc_type": ioc_type})
            self.add_relationship(alert_id, "alert", ioc_val, "ioc", "observed_in")

        logger.debug(f"KG ingested alert {alert_id}: nodes={self._stats['nodes']} edges={self._stats['edges']}")

    def ingest_incident(self, incident: Dict) -> None:
        """Ingest an incident and link to related alerts."""
        if not self.available:
            return

        inc_id = str(incident.get("id", "unknown"))
        self.add_entity(inc_id, "incident", {
            "title":    incident.get("title", ""),
            "severity": incident.get("severity", "medium"),
            "status":   incident.get("status", "open"),
        })

        for alert_id in (incident.get("related_alert_ids") or []):
            self.add_relationship(str(alert_id), "alert", inc_id, "incident", "escalated_to")

    # ── Rich Demo Seed Data ────────────────────────────────────────────

    def seed_demo_data(self) -> None:
        """Seed with full threat-intelligence relationships for demo / hackathon."""
        if not self.available or self._stats["nodes"] > 100:
            return

        logger.info("🌱 Seeding Security Knowledge Graph with rich threat-intel data…")

        # ── MITRE Tactics ───────────────────────────────────────────────
        tactics = [
            ("Initial Access",      "TA0001"),
            ("Execution",           "TA0002"),
            ("Persistence",         "TA0003"),
            ("Privilege Escalation","TA0004"),
            ("Defense Evasion",     "TA0005"),
            ("Credential Access",   "TA0006"),
            ("Discovery",           "TA0007"),
            ("Lateral Movement",    "TA0008"),
            ("Collection",          "TA0009"),
            ("Exfiltration",        "TA0010"),
            ("Impact",              "TA0040"),
            ("Command and Control", "TA0011"),
        ]
        for name, tid in tactics:
            self.add_entity(tid, "mitre_tactic", {"name": name, "tactic_id": tid})

        # ── MITRE Techniques ────────────────────────────────────────────
        techniques = [
            ("T1110", "Brute Force",                    "TA0006"),
            ("T1190", "Exploit Public-Facing App",      "TA0001"),
            ("T1486", "Data Encrypted for Impact",      "TA0040"),
            ("T1059", "Command-Line Interface",         "TA0002"),
            ("T1055", "Process Injection",              "TA0004"),
            ("T1021", "Remote Services",                "TA0008"),
            ("T1078", "Valid Accounts",                 "TA0003"),
            ("T1003", "OS Credential Dumping",          "TA0006"),
            ("T1071", "Application Layer Protocol",     "TA0011"),
            ("T1566", "Phishing",                       "TA0001"),
            ("T1082", "System Information Discovery",   "TA0007"),
            ("T1041", "Exfiltration Over C2 Channel",  "TA0010"),
            ("T1070", "Indicator Removal on Host",      "TA0005"),
            ("T1136", "Create Account",                 "TA0003"),
        ]
        for tid, name, tactic_id in techniques:
            self.add_entity(tid, "mitre_technique", {"name": name, "technique_id": tid})
            self.add_relationship(tid, "mitre_technique", tactic_id, "mitre_tactic", "belongs_to")

        # ── Threat Actors ───────────────────────────────────────────────
        threat_actors = [
            ("APT29",    {"name": "Cozy Bear",       "origin": "Russia",       "motivation": "Espionage",       "sophistication": "very-high"}),
            ("APT28",    {"name": "Fancy Bear",      "origin": "Russia",       "motivation": "Espionage",       "sophistication": "very-high"}),
            ("Lazarus",  {"name": "Lazarus Group",   "origin": "North Korea",  "motivation": "Financial/Sabotage","sophistication": "high"}),
            ("FIN7",     {"name": "FIN7 / Carbanak", "origin": "Eastern Europe","motivation": "Financial",      "sophistication": "high"}),
            ("DarkSide", {"name": "DarkSide RaaS",   "origin": "Unknown",      "motivation": "Ransomware",      "sophistication": "medium"}),
        ]
        for actor_id, props in threat_actors:
            self.add_entity(actor_id, "threat_actor", props)

        # ── Malware Families ────────────────────────────────────────────
        malware_list = [
            ("WannaCry",     {"type": "Ransomware",        "family": "WannaCry",      "hash": "db349b97c37d22f5ea1d1841e3c89eb4"}),
            ("Emotet",       {"type": "Botnet/Trojan",     "family": "Emotet",        "c2": "185.220.101.34"}),
            ("CobaltStrike", {"type": "C2 Framework",      "family": "CobaltStrike",  "version": "4.x"}),
            ("BlackCat",     {"type": "Ransomware",        "family": "ALPHV/BlackCat","language": "Rust"}),
            ("Mimikatz",     {"type": "Credential Dumper", "family": "Mimikatz",      "hash": "92b70a0cb82e3be2bf17b7af6c90c9d4"}),
            ("Cobalt",       {"type": "Banking Trojan",    "family": "Carbanak",      "target": "Finance"}),
        ]
        for mal_id, props in malware_list:
            self.add_entity(mal_id, "malware", props)

        # ── CVEs / Vulnerabilities ──────────────────────────────────────
        cves = [
            ("CVE-2021-44228", {"name": "Log4Shell",        "cvss": 10.0, "affected_software": "Apache Log4j 2.x",    "kev": True}),
            ("CVE-2023-34362", {"name": "MOVEit RCE",       "cvss": 9.8,  "affected_software": "Progress MOVEit",     "kev": True}),
            ("CVE-2021-26855", {"name": "ProxyLogon",       "cvss": 9.8,  "affected_software": "MS Exchange Server",  "kev": True}),
            ("CVE-2022-30190", {"name": "Follina",          "cvss": 7.8,  "affected_software": "Microsoft Office",    "kev": True}),
            ("CVE-2019-0708",  {"name": "BlueKeep",        "cvss": 9.8,  "affected_software": "Windows RDP",          "kev": True}),
            ("CVE-2021-34527", {"name": "PrintNightmare",  "cvss": 8.8,  "affected_software": "Windows Print Spooler","kev": True}),
        ]
        for cve_id, props in cves:
            self.add_entity(cve_id, "cve", props)

        # ── Software ────────────────────────────────────────────────────
        software_list = [
            ("Apache_Log4j",  {"name": "Apache Log4j",   "version": "2.14.1", "vendor": "Apache"}),
            ("MS_Exchange",   {"name": "MS Exchange",    "version": "2019",   "vendor": "Microsoft"}),
            ("MS_Office",     {"name": "MS Office",      "version": "2019",   "vendor": "Microsoft"}),
            ("OpenSSH",       {"name": "OpenSSH",        "version": "8.4",    "vendor": "OpenBSD"}),
            ("Windows_RDP",   {"name": "Windows RDP",    "version": "10",     "vendor": "Microsoft"}),
        ]
        for sw_id, props in software_list:
            self.add_entity(sw_id, "software", props)

        # ── Assets ──────────────────────────────────────────────────────
        assets = [
            ("prod-db-01",       {"criticality": "critical", "os": "Linux",   "owner": "IT Ops",    "ip": "10.0.1.10"}),
            ("hr-fileshare",     {"criticality": "high",     "os": "Windows", "owner": "HR Dept",   "ip": "10.0.2.20"}),
            ("web-app-prod",     {"criticality": "critical", "os": "Linux",   "owner": "Dev Team",  "ip": "10.0.3.30"}),
            ("mail-server-01",   {"criticality": "high",     "os": "Windows", "owner": "IT Ops",    "ip": "10.0.1.50"}),
            ("dc-01",            {"criticality": "critical", "os": "Windows", "owner": "IT Ops",    "ip": "10.0.0.1", "type": "Domain Controller"}),
            ("backup-server-01", {"criticality": "high",     "os": "Linux",   "owner": "IT Ops",    "ip": "10.0.5.10"}),
        ]
        for asset_id, props in assets:
            self.add_entity(asset_id, "asset", props)

        # ── Applications ────────────────────────────────────────────────
        apps = [
            ("web-portal",   {"name": "Customer Web Portal",  "owner": "Dev Team",  "criticality": "high"}),
            ("hr-system",    {"name": "HR Management System", "owner": "HR Dept",   "criticality": "medium"}),
            ("finance-app",  {"name": "Finance ERP",          "owner": "Finance",   "criticality": "critical"}),
            ("siem-tool",    {"name": "SIEM Platform",        "owner": "SOC Team",  "criticality": "critical"}),
        ]
        for app_id, props in apps:
            self.add_entity(app_id, "application", props)

        # ── Users ───────────────────────────────────────────────────────
        users = [
            ("alice.smith", {"role": "Admin",    "department": "IT",      "risk_score": 0.3,  "mfa": True}),
            ("bob.jones",   {"role": "User",     "department": "HR",      "risk_score": 0.2,  "mfa": False}),
            ("carol.exec",  {"role": "C-Level",  "department": "Finance", "risk_score": 0.4,  "mfa": True}),
            ("dave.dev",    {"role": "Developer","department": "Engineering","risk_score": 0.35,"mfa": True}),
            ("eve.malicious",{"role": "Threat Actor","department": "External","risk_score": 0.95,"mfa": False}),
        ]
        for user_id, props in users:
            self.add_entity(user_id, "user", props)

        # ── Devices ─────────────────────────────────────────────────────
        devices = [
            ("DESKTOP-ALICE",  {"os": "Windows 11", "owner": "alice.smith", "ip": "10.0.10.5"}),
            ("LAPTOP-BOB",     {"os": "Windows 10", "owner": "bob.jones",   "ip": "10.0.10.6"}),
            ("WORKSTATION-DEV",{"os": "Ubuntu 22",  "owner": "dave.dev",    "ip": "10.0.10.7"}),
        ]
        for dev_id, props in devices:
            self.add_entity(dev_id, "device", props)

        # ── IOCs ────────────────────────────────────────────────────────
        iocs = [
            ("185.220.101.34",                    {"ioc_type": "ip",     "reputation": "malicious", "source": "ThreatFox"}),
            ("evil-c2.onion",                     {"ioc_type": "domain", "reputation": "malicious", "source": "MISP"}),
            ("db349b97c37d22f5ea1d1841e3c89eb4",  {"ioc_type": "hash",   "algorithm": "MD5",        "source": "VirusTotal"}),
            ("92b70a0cb82e3be2bf17b7af6c90c9d4",  {"ioc_type": "hash",   "algorithm": "MD5",        "source": "VirusTotal"}),
            ("194.165.16.45",                     {"ioc_type": "ip",     "reputation": "malicious", "source": "CISA"}),
        ]
        for ioc_id, props in iocs:
            self.add_entity(ioc_id, "ioc", props)

        # ── Security Controls ───────────────────────────────────────────
        controls = [
            ("MFA",          {"name": "Multi-Factor Authentication", "type": "preventive",  "status": "implemented"}),
            ("EDR",          {"name": "Endpoint Detection & Response","type": "detective",   "status": "implemented"}),
            ("SIEM",         {"name": "SIEM / Log Aggregation",      "type": "detective",   "status": "implemented"}),
            ("DLP",          {"name": "Data Loss Prevention",        "type": "preventive",  "status": "partial"}),
            ("FIREWALL",     {"name": "Perimeter Firewall",          "type": "preventive",  "status": "implemented"}),
            ("PAM",          {"name": "Privileged Access Management","type": "preventive",  "status": "not-implemented"}),
            ("VULN-SCAN",    {"name": "Vulnerability Scanner",       "type": "detective",   "status": "implemented"}),
            ("BACKUP",       {"name": "Immutable Backup System",     "type": "corrective",  "status": "partial"}),
        ]
        for ctrl_id, props in controls:
            self.add_entity(ctrl_id, "security_control", props)

        # ── Compliance Controls ─────────────────────────────────────────
        comp_controls = [
            ("NIST-PR.AC-1",  {"framework": "NIST CSF",   "name": "Identity & Access Management",   "status": "compliant"}),
            ("NIST-DE.CM-1",  {"framework": "NIST CSF",   "name": "Network Monitoring",              "status": "compliant"}),
            ("CIS-1",         {"framework": "CIS Controls","name": "Inventory of Enterprise Assets", "status": "partial"}),
            ("CIS-5",         {"framework": "CIS Controls","name": "Account Management",             "status": "compliant"}),
            ("PCI-DSS-6",     {"framework": "PCI DSS",    "name": "Vulnerability Management",       "status": "partial"}),
            ("ISO-A.9.1",     {"framework": "ISO 27001",  "name": "Access Control Policy",          "status": "compliant"}),
        ]
        for cc_id, props in comp_controls:
            self.add_entity(cc_id, "compliance_control", props)

        # ── Demo Incidents ──────────────────────────────────────────────
        incidents = [
            ("INC-001", {"title": "Ransomware Outbreak on HR Share",     "severity": "critical", "status": "open"}),
            ("INC-002", {"title": "APT29 Credential Theft Campaign",     "severity": "critical", "status": "investigating"}),
            ("INC-003", {"title": "Log4Shell Exploitation on Web App",   "severity": "high",     "status": "contained"}),
            ("INC-004", {"title": "Lateral Movement from Compromised HR","severity": "high",     "status": "open"}),
        ]
        for inc_id, props in incidents:
            self.add_entity(inc_id, "incident", props)

        # ═══════════════════════════════════════════════════════════════
        # RELATIONSHIPS  (50+)
        # ═══════════════════════════════════════════════════════════════

        # Threat Actor → uses → Malware
        self.add_relationship("Lazarus",  "threat_actor", "WannaCry",     "malware", "uses")
        self.add_relationship("APT29",    "threat_actor", "CobaltStrike", "malware", "uses")
        self.add_relationship("FIN7",     "threat_actor", "Cobalt",       "malware", "uses")
        self.add_relationship("DarkSide", "threat_actor", "BlackCat",     "malware", "uses")
        self.add_relationship("APT28",    "threat_actor", "Mimikatz",     "malware", "uses")

        # Threat Actor → exploits → CVE
        self.add_relationship("Lazarus",  "threat_actor", "CVE-2021-44228", "cve", "exploits")
        self.add_relationship("APT29",    "threat_actor", "CVE-2021-26855", "cve", "exploits")
        self.add_relationship("APT28",    "threat_actor", "CVE-2022-30190", "cve", "exploits")
        self.add_relationship("FIN7",     "threat_actor", "CVE-2019-0708",  "cve", "exploits")

        # Threat Actor → uses → Technique
        self.add_relationship("APT29",    "threat_actor", "T1078", "mitre_technique", "uses")
        self.add_relationship("APT29",    "threat_actor", "T1003", "mitre_technique", "uses")
        self.add_relationship("APT28",    "threat_actor", "T1566", "mitre_technique", "uses")
        self.add_relationship("Lazarus",  "threat_actor", "T1486", "mitre_technique", "uses")
        self.add_relationship("FIN7",     "threat_actor", "T1059", "mitre_technique", "uses")
        self.add_relationship("DarkSide", "threat_actor", "T1486", "mitre_technique", "uses")

        # Malware → implements → Technique
        self.add_relationship("WannaCry",     "malware", "T1486", "mitre_technique", "implements")
        self.add_relationship("CobaltStrike", "malware", "T1190", "mitre_technique", "implements")
        self.add_relationship("CobaltStrike", "malware", "T1071", "mitre_technique", "implements")
        self.add_relationship("Mimikatz",     "malware", "T1003", "mitre_technique", "implements")
        self.add_relationship("BlackCat",     "malware", "T1486", "mitre_technique", "implements")
        self.add_relationship("Emotet",       "malware", "T1566", "mitre_technique", "implements")

        # Malware → c2_communicates_with → IOC
        self.add_relationship("Emotet",       "malware", "evil-c2.onion",     "ioc", "c2_communicates_with")
        self.add_relationship("CobaltStrike", "malware", "185.220.101.34",    "ioc", "c2_communicates_with")

        # Malware → hash_matches → IOC
        self.add_relationship("WannaCry", "malware", "db349b97c37d22f5ea1d1841e3c89eb4", "ioc", "hash_matches")
        self.add_relationship("Mimikatz", "malware", "92b70a0cb82e3be2bf17b7af6c90c9d4", "ioc", "hash_matches")

        # CVE → affects → Software
        self.add_relationship("CVE-2021-44228", "cve", "Apache_Log4j", "software", "affects")
        self.add_relationship("CVE-2021-26855", "cve", "MS_Exchange",  "software", "affects")
        self.add_relationship("CVE-2022-30190", "cve", "MS_Office",    "software", "affects")
        self.add_relationship("CVE-2019-0708",  "cve", "Windows_RDP",  "software", "affects")
        self.add_relationship("CVE-2021-34527", "cve", "Windows_RDP",  "software", "affects")

        # Software → deployed_on → Asset
        self.add_relationship("Apache_Log4j", "software", "web-app-prod",   "asset", "deployed_on")
        self.add_relationship("MS_Exchange",  "software", "mail-server-01", "asset", "deployed_on")
        self.add_relationship("Windows_RDP",  "software", "dc-01",          "asset", "deployed_on")

        # Asset → vulnerable_to → CVE
        self.add_relationship("web-app-prod",   "asset", "CVE-2021-44228", "cve", "vulnerable_to")
        self.add_relationship("mail-server-01", "asset", "CVE-2021-26855", "cve", "vulnerable_to")
        self.add_relationship("hr-fileshare",   "asset", "CVE-2021-34527", "cve", "vulnerable_to")
        self.add_relationship("dc-01",          "asset", "CVE-2019-0708",  "cve", "vulnerable_to")

        # Asset → hosts → Application
        self.add_relationship("web-app-prod",   "asset", "web-portal",  "application", "hosts")
        self.add_relationship("hr-fileshare",   "asset", "hr-system",   "application", "hosts")
        self.add_relationship("prod-db-01",     "asset", "finance-app", "application", "hosts")

        # User → logged_into → Device
        self.add_relationship("alice.smith", "user", "DESKTOP-ALICE",   "device", "logged_into")
        self.add_relationship("bob.jones",   "user", "LAPTOP-BOB",      "device", "logged_into")
        self.add_relationship("dave.dev",    "user", "WORKSTATION-DEV", "device", "logged_into")

        # User → administers/accesses → Asset
        self.add_relationship("alice.smith", "user", "prod-db-01",     "asset", "administers")
        self.add_relationship("alice.smith", "user", "dc-01",          "asset", "administers")
        self.add_relationship("bob.jones",   "user", "hr-fileshare",   "asset", "accesses")
        self.add_relationship("carol.exec",  "user", "finance-app",    "application", "accesses")
        self.add_relationship("dave.dev",    "user", "web-app-prod",   "asset", "administers")

        # Device → connected_to → Asset
        self.add_relationship("DESKTOP-ALICE",   "device", "dc-01",        "asset", "connected_to")
        self.add_relationship("LAPTOP-BOB",      "device", "hr-fileshare", "asset", "connected_to")
        self.add_relationship("WORKSTATION-DEV", "device", "web-app-prod", "asset", "connected_to")

        # Device → lateral_move_to → Device (lateral movement chain)
        self.add_relationship("LAPTOP-BOB",      "device", "hr-fileshare",   "asset", "lateral_move_to")
        self.add_relationship("hr-fileshare",    "asset",  "dc-01",          "asset", "lateral_move_to")
        self.add_relationship("dc-01",           "asset",  "backup-server-01","asset","lateral_move_to")

        # Incident → involves → Malware
        self.add_relationship("INC-001", "incident", "WannaCry",     "malware",       "involves")
        self.add_relationship("INC-002", "incident", "CobaltStrike", "malware",       "involves")
        self.add_relationship("INC-002", "incident", "Mimikatz",     "malware",       "involves")
        self.add_relationship("INC-003", "incident", "CVE-2021-44228","cve",          "involves")

        # Incident → affects → Asset
        self.add_relationship("INC-001", "incident", "hr-fileshare",   "asset", "affects")
        self.add_relationship("INC-002", "incident", "dc-01",          "asset", "affects")
        self.add_relationship("INC-003", "incident", "web-app-prod",   "asset", "affects")
        self.add_relationship("INC-004", "incident", "prod-db-01",     "asset", "affects")

        # Incident → attributed_to → Threat Actor
        self.add_relationship("INC-001", "incident", "Lazarus", "threat_actor", "attributed_to")
        self.add_relationship("INC-002", "incident", "APT29",   "threat_actor", "attributed_to")
        self.add_relationship("INC-004", "incident", "FIN7",    "threat_actor", "attributed_to")

        # Incident → matches → MITRE Technique
        self.add_relationship("INC-001", "incident", "T1486", "mitre_technique", "matches")
        self.add_relationship("INC-002", "incident", "T1078", "mitre_technique", "matches")
        self.add_relationship("INC-002", "incident", "T1003", "mitre_technique", "matches")
        self.add_relationship("INC-004", "incident", "T1021", "mitre_technique", "matches")

        # IOC → observed_in → Alert (demo alerts)
        self.add_relationship("185.220.101.34", "ioc", "alert_demo_1", "alert", "observed_in")

        # Security Control → mitigates → Technique
        self.add_relationship("MFA",      "security_control", "T1078", "mitre_technique", "mitigates")
        self.add_relationship("EDR",      "security_control", "T1055", "mitre_technique", "mitigates")
        self.add_relationship("FIREWALL", "security_control", "T1190", "mitre_technique", "mitigates")
        self.add_relationship("DLP",      "security_control", "T1041", "mitre_technique", "mitigates")
        self.add_relationship("BACKUP",   "security_control", "T1486", "mitre_technique", "mitigates")
        self.add_relationship("PAM",      "security_control", "T1003", "mitre_technique", "mitigates")

        # Security Control → prevents → CVE
        self.add_relationship("VULN-SCAN", "security_control", "CVE-2021-44228", "cve", "detects")
        self.add_relationship("FIREWALL",  "security_control", "CVE-2019-0708",  "cve", "prevents")

        # Compliance Control → maps_to → Security Control
        self.add_relationship("NIST-PR.AC-1", "compliance_control", "MFA",    "security_control", "maps_to_control")
        self.add_relationship("NIST-PR.AC-1", "compliance_control", "PAM",    "security_control", "maps_to_control")
        self.add_relationship("NIST-DE.CM-1", "compliance_control", "SIEM",   "security_control", "maps_to_control")
        self.add_relationship("CIS-5",        "compliance_control", "MFA",    "security_control", "maps_to_control")
        self.add_relationship("PCI-DSS-6",    "compliance_control", "VULN-SCAN","security_control","maps_to_control")

        # Threat Actor → operates_from (external IP) → IOC
        self.add_relationship("APT29",    "threat_actor", "194.165.16.45",  "ioc", "operates_from")
        self.add_relationship("Lazarus",  "threat_actor", "185.220.101.34", "ioc", "operates_from")

        logger.info(
            f"✅ KG seeded: {self._stats['nodes']} nodes, {self._stats['edges']} edges"
        )

    # ── Queries ────────────────────────────────────────────────────────

    def get_entity_context(self, entity_id: str, entity_type: str, max_depth: int = 2) -> Dict:
        """Get full context of an entity — all connected nodes up to max_depth (BFS)."""
        if not self.available:
            return {"entity": f"{entity_type}:{entity_id}", "related": [], "paths": []}

        self._stats["queries"] += 1
        node = f"{entity_type}:{entity_id}"

        if node not in self._graph:
            return {"entity": node, "related": [], "paths": []}

        related = []
        visited = {node}
        queue = [(node, 0)]

        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            for _, neighbor, data in self._graph.out_edges(current, data=True):
                if neighbor not in visited:
                    visited.add(neighbor)
                    ndata = self._graph.nodes[neighbor]
                    related.append({
                        "entity": neighbor,
                        "type": ndata.get("entity_type", "unknown"),
                        "relation": data.get("relation", "connected"),
                        "direction": "outgoing",
                        "depth": depth + 1,
                        "properties": ndata.get("properties", {}),
                    })
                    queue.append((neighbor, depth + 1))

            for predecessor, _, data in self._graph.in_edges(current, data=True):
                if predecessor not in visited:
                    visited.add(predecessor)
                    pdata = self._graph.nodes[predecessor]
                    related.append({
                        "entity": predecessor,
                        "type": pdata.get("entity_type", "unknown"),
                        "relation": data.get("relation", "connected"),
                        "direction": "incoming",
                        "depth": depth + 1,
                        "properties": pdata.get("properties", {}),
                    })
                    queue.append((predecessor, depth + 1))

        return {
            "entity": node,
            "node_properties": self._graph.nodes[node].get("properties", {}),
            "related_count": len(related),
            "related": related,
        }

    def get_ip_threat_profile(self, ip: str) -> Dict:
        """Get all threat activity associated with an IP address."""
        context = self.get_entity_context(ip, "ip", max_depth=2)
        related  = context.get("related", [])
        alerts    = [r for r in related if r["type"] == "alert"]
        techniques = [r for r in related if r["type"] == "mitre_technique"]
        users_targeted = [r for r in related if r["type"] == "user"]
        devices   = [r for r in related if r["type"] == "device"]
        iocs      = [r for r in related if r["type"] == "ioc"]

        return {
            "ip": ip,
            "total_alerts": len(alerts),
            "alerts": alerts,
            "mitre_techniques": [t["entity"].split(":")[1] for t in techniques],
            "users_targeted": [u["entity"].split(":")[1] for u in users_targeted],
            "devices_affected": [d["entity"].split(":")[1] for d in devices],
            "iocs": [i["entity"].split(":")[1] for i in iocs],
            "risk_score": min(1.0, len(alerts) * 0.15 + len(techniques) * 0.1 + len(iocs) * 0.2),
            "communicates_with": [
                r["entity"].split(":")[1] for r in related
                if r["type"] == "ip" and r["relation"] == "communicates_with"
            ],
        }

    def get_attack_path(self, source: str, source_type: str, target: str, target_type: str) -> List[Dict]:
        """Find attack paths between any two entities."""
        if not self.available:
            return []

        src = f"{source_type}:{source}"
        tgt = f"{target_type}:{target}"

        if src not in self._graph or tgt not in self._graph:
            return []

        # Use an undirected view for path finding (attacks can traverse any direction)
        ug = self._graph.to_undirected()
        try:
            paths = list(nx.all_simple_paths(ug, src, tgt, cutoff=6))
            result = []
            for path in paths[:5]:
                path_detail = []
                for i in range(len(path) - 1):
                    edge_data = self._graph.get_edge_data(path[i], path[i + 1]) or {}
                    # MultiDiGraph: get_edge_data returns dict of key→data
                    rel = "connected"
                    if edge_data:
                        first_edge = list(edge_data.values())[0] if isinstance(edge_data, dict) else edge_data
                        rel = first_edge.get("relation", "connected") if isinstance(first_edge, dict) else "connected"
                    path_detail.append({"from": path[i], "to": path[i + 1], "relation": rel})
                result.append({"path": path, "edges": path_detail, "length": len(path)})
            return result
        except nx.NetworkXError:
            return []

    # ── Risk Propagation ───────────────────────────────────────────────

    def propagate_risk(self, entity_id: str, entity_type: str, initial_score: float = 0.9) -> Dict:
        """
        Cascade risk from a compromised entity through the graph.
        Returns all affected entities with propagated risk scores.
        """
        if not self.available:
            return {}

        start_node = f"{entity_type}:{entity_id}"
        if start_node not in self._graph:
            return {}

        # BFS risk propagation with decay factor
        DECAY = 0.6
        risk_map: Dict[str, float] = {start_node: initial_score}
        queue = [(start_node, initial_score)]
        visited = {start_node}

        while queue:
            current, risk = queue.pop(0)
            if risk < 0.05:
                continue

            propagated = risk * DECAY
            node_type = self._graph.nodes[current].get("entity_type", "")

            # High-value targets amplify risk
            props = self._graph.nodes[current].get("properties", {})
            if props.get("criticality") in ("critical", "high"):
                propagated = min(propagated * 1.2, 1.0)

            for _, neighbor, data in self._graph.out_edges(current, data=True):
                rel = data.get("relation", "")
                # Only propagate through meaningful relationships
                if rel in ("lateral_move_to", "connected_to", "hosts", "accesses",
                           "administers", "logged_into", "runs", "deployed_on"):
                    if neighbor not in visited or risk_map.get(neighbor, 0) < propagated:
                        visited.add(neighbor)
                        risk_map[neighbor] = round(propagated, 3)
                        queue.append((neighbor, propagated))

        # Format results
        result = []
        for node, score in sorted(risk_map.items(), key=lambda x: -x[1]):
            if node == start_node:
                continue
            ndata = self._graph.nodes.get(node, {})
            result.append({
                "entity": node,
                "type": ndata.get("entity_type", "unknown"),
                "risk_score": score,
                "properties": ndata.get("properties", {}),
                "risk_level": "critical" if score > 0.7 else "high" if score > 0.4 else "medium" if score > 0.2 else "low",
            })

        return {
            "source": start_node,
            "initial_score": initial_score,
            "affected_entities": result,
            "total_affected": len(result),
            "blast_radius": {
                "critical": sum(1 for r in result if r["risk_level"] == "critical"),
                "high":     sum(1 for r in result if r["risk_level"] == "high"),
                "medium":   sum(1 for r in result if r["risk_level"] == "medium"),
                "low":      sum(1 for r in result if r["risk_level"] == "low"),
            },
        }

    # ── Threat Hunting Queries ─────────────────────────────────────────

    def hunt_lateral_movement(self) -> List[Dict]:
        """Identify lateral movement chains in the graph."""
        if not self.available:
            return []

        chains = []
        for src, tgt, data in self._graph.edges(data=True):
            if data.get("relation") == "lateral_move_to":
                src_data = self._graph.nodes.get(src, {})
                tgt_data = self._graph.nodes.get(tgt, {})
                chains.append({
                    "from_entity":  src,
                    "to_entity":    tgt,
                    "from_type":    src_data.get("entity_type", "unknown"),
                    "to_type":      tgt_data.get("entity_type", "unknown"),
                    "from_props":   src_data.get("properties", {}),
                    "to_props":     tgt_data.get("properties", {}),
                    "risk":         "high",
                })
        return chains

    def hunt_devices_with_malicious_ips(self) -> List[Dict]:
        """Find devices/assets that have communicated with known malicious IPs."""
        if not self.available:
            return []

        malicious_iocs = {
            n for n, d in self._graph.nodes(data=True)
            if d.get("entity_type") == "ioc"
            and d.get("properties", {}).get("reputation") == "malicious"
        }

        results = []
        for ioc_node in malicious_iocs:
            # Find any entity that communicates with or is connected to this IOC
            for src, _, data in self._graph.in_edges(ioc_node, data=True):
                src_data = self._graph.nodes.get(src, {})
                src_type = src_data.get("entity_type", "")
                if src_type in ("device", "asset", "user", "ip", "malware"):
                    results.append({
                        "entity": src,
                        "type": src_type,
                        "malicious_ioc": ioc_node,
                        "relation": data.get("relation", "connected"),
                        "properties": src_data.get("properties", {}),
                        "threat": "high",
                    })
        return results

    def hunt_users_with_multiple_incidents(self) -> List[Dict]:
        """Find users associated with multiple security incidents."""
        if not self.available:
            return []

        user_incidents: Dict[str, List[str]] = defaultdict(list)

        for node, data in self._graph.nodes(data=True):
            if data.get("entity_type") == "incident":
                # Walk outgoing edges to find affected users
                ctx = self.get_entity_context(
                    data.get("entity_id", node.split(":", 1)[-1]),
                    "incident", max_depth=2
                )
                for r in ctx.get("related", []):
                    if r["type"] == "user":
                        user_id = r["entity"].split(":", 1)[-1]
                        user_incidents[user_id].append(node)

        results = []
        for user, incs in user_incidents.items():
            if len(incs) > 1:
                unode = f"user:{user}"
                udata = self._graph.nodes.get(unode, {})
                results.append({
                    "user": user,
                    "incident_count": len(incs),
                    "incidents": incs,
                    "risk_score": min(1.0, 0.3 * len(incs)),
                    "properties": udata.get("properties", {}),
                })
        return sorted(results, key=lambda x: -x["incident_count"])

    def hunt_vulnerable_connected_assets(self) -> List[Dict]:
        """Find assets that are vulnerable AND connected to other critical assets."""
        if not self.available:
            return []

        results = []
        for node, data in self._graph.nodes(data=True):
            if data.get("entity_type") not in ("asset", "device"):
                continue

            # Check if vulnerable
            cves = [
                tgt for _, tgt, edata in self._graph.out_edges(node, data=True)
                if edata.get("relation") == "vulnerable_to"
            ]
            if not cves:
                continue

            # Check connections to other assets
            connected = [
                tgt for _, tgt, edata in self._graph.out_edges(node, data=True)
                if edata.get("relation") in ("connected_to", "lateral_move_to", "hosts")
                and self._graph.nodes.get(tgt, {}).get("entity_type") in ("asset", "device")
            ]

            if connected:
                props = data.get("properties", {})
                results.append({
                    "entity": node,
                    "type": data.get("entity_type"),
                    "cves": [c.split(":", 1)[-1] for c in cves],
                    "connected_assets": [c.split(":", 1)[-1] for c in connected],
                    "criticality": props.get("criticality", "unknown"),
                    "risk": "critical" if props.get("criticality") == "critical" else "high",
                    "properties": props,
                })
        return sorted(results, key=lambda x: 0 if x["risk"] == "critical" else 1)

    def get_mitre_coverage(self) -> Dict:
        """Return which techniques are covered by security controls vs. actively used by threat actors."""
        if not self.available:
            return {}

        covered_techniques = set()
        for src, tgt, data in self._graph.edges(data=True):
            if data.get("relation") in ("mitigates", "detects", "prevents"):
                tgt_data = self._graph.nodes.get(tgt, {})
                if tgt_data.get("entity_type") == "mitre_technique":
                    covered_techniques.add(tgt.split(":", 1)[-1])

        used_techniques = set()
        for src, tgt, data in self._graph.edges(data=True):
            if data.get("relation") == "uses":
                src_data = self._graph.nodes.get(src, {})
                tgt_data = self._graph.nodes.get(tgt, {})
                if src_data.get("entity_type") == "threat_actor" and tgt_data.get("entity_type") == "mitre_technique":
                    used_techniques.add(tgt.split(":", 1)[-1])

        uncovered = used_techniques - covered_techniques
        return {
            "total_techniques": len(used_techniques),
            "covered": len(covered_techniques & used_techniques),
            "uncovered_count": len(uncovered),
            "uncovered_techniques": list(uncovered),
            "coverage_pct": round(len(covered_techniques & used_techniques) / max(len(used_techniques), 1) * 100, 1),
        }

    # ── GraphRAG Context ───────────────────────────────────────────────

    def get_graph_context_for_query(self, query: str, max_entities: int = 8) -> str:
        """
        Extract relevant graph context for an LLM query.
        Matches entity mentions in the query and returns their graph neighbourhoods.
        Used by GraphRAG fusion to enrich agent prompts.
        """
        if not self.available:
            return ""

        query_lower = query.lower()
        matched_nodes = []

        for node, data in self._graph.nodes(data=True):
            entity_id = data.get("entity_id", "").lower()
            props = data.get("properties", {})
            name  = str(props.get("name", "")).lower()

            if entity_id in query_lower or (name and name in query_lower):
                matched_nodes.append(node)

        if not matched_nodes:
            # Return summary of high-risk entities when nothing matched
            high_risk = [
                (n, d) for n, d in self._graph.nodes(data=True)
                if d.get("properties", {}).get("risk_score", 0) > 0.6
                   or d.get("properties", {}).get("criticality") == "critical"
            ][:max_entities]
            if not high_risk:
                return ""
            context = "## Graph Context (High-Risk Entities)\n"
            for n, d in high_risk:
                context += f"- {n} | {d.get('properties', {})}\n"
            return context

        context_parts = ["## Security Knowledge Graph Context"]
        seen = set()

        for node in matched_nodes[:max_entities]:
            if node in seen:
                continue
            seen.add(node)

            ndata = self._graph.nodes[node]
            entity_id_str = ndata.get("entity_id", node)
            etype = ndata.get("entity_type", "unknown")
            props = ndata.get("properties", {})

            context_parts.append(f"\n### {etype.upper()}: {entity_id_str}")
            for k, v in list(props.items())[:5]:
                context_parts.append(f"  {k}: {v}")

            # Outgoing relationships
            out_rels = []
            for _, tgt, edata in self._graph.out_edges(node, data=True):
                rel = edata.get("relation", "→")
                out_rels.append(f"  → [{rel}] → {tgt}")
            if out_rels:
                context_parts.append("  Relationships:")
                context_parts.extend(out_rels[:6])

        return "\n".join(context_parts)

    # ── Stats & Visualization ─────────────────────────────────────────

    def get_graph_stats(self) -> Dict:
        if not self.available:
            return {"available": False, "reason": "networkx not installed"}

        type_counts: Dict[str, int] = defaultdict(int)
        for _, data in self._graph.nodes(data=True):
            type_counts[data.get("entity_type", "unknown")] += 1

        relation_counts: Dict[str, int] = defaultdict(int)
        for _, _, data in self._graph.edges(data=True):
            relation_counts[data.get("relation", "unknown")] += 1

        return {
            "available": True,
            "total_nodes":        self._graph.number_of_nodes(),
            "total_edges":        self._graph.number_of_edges(),
            "node_types":         dict(type_counts),
            "relationship_types": dict(relation_counts),
            "queries_served":     self._stats["queries"],
        }

    def get_graph_visualization_data(self) -> Dict:
        """Export enriched graph data for frontend force-graph visualization."""
        if not self.available:
            return {"nodes": [], "edges": []}

        nodes = []
        for node_id, data in self._graph.nodes(data=True):
            etype = data.get("entity_type", "unknown")
            props = data.get("properties", {})
            nodes.append({
                "id":         node_id,
                "type":       etype,
                "label":      data.get("entity_id", node_id),
                "color":      ENTITY_COLORS.get(etype, "#9ca3af"),
                "properties": props,
                "risk_score": float(props.get("risk_score", 0) or 0),
                "criticality":props.get("criticality", ""),
            })

        edges = []
        for src, tgt, data in self._graph.edges(data=True):
            edges.append({
                "source":   src,
                "target":   tgt,
                "relation": data.get("relation", "connected"),
            })

        return {"nodes": nodes, "edges": edges}


# ── Singleton ────────────────────────────────────────────────────────────

_kg_instance: Optional[SecurityKnowledgeGraph] = None


def get_knowledge_graph() -> SecurityKnowledgeGraph:
    """Get the singleton knowledge graph instance."""
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = SecurityKnowledgeGraph()
        logger.info(f"✅ Knowledge graph initialized (networkx: {HAS_NETWORKX})")
    return _kg_instance
