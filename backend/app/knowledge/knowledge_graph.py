"""
SecureFlow AI — Security Knowledge Graph
In-memory graph that maps relationships between security entities.
Uses networkx for graph operations.

Nodes: IPs, Users, Devices, Alerts, Incidents, MITRE Techniques, IOCs
Edges: triggered, targets, maps_to, communicates_with, escalated_to, logged_into
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("networkx not installed — knowledge graph disabled. Install with: pip install networkx")


class SecurityKnowledgeGraph:
    """
    Security-focused knowledge graph that tracks relationships between
    IPs, users, alerts, incidents, MITRE techniques, and IOCs.
    
    Enables:
    - Attack path reconstruction
    - Blast radius analysis  
    - Threat actor correlation
    - Entity risk scoring
    """

    def __init__(self):
        if HAS_NETWORKX:
            self._graph = nx.DiGraph()
        else:
            self._graph = None
        self._stats = {"nodes": 0, "edges": 0, "queries": 0}

    @property
    def available(self) -> bool:
        return HAS_NETWORKX and self._graph is not None

    # ── Node Management ──────────────────────────────────────────────

    def add_entity(self, entity_id: str, entity_type: str, properties: Dict = None):
        """Add a node to the knowledge graph."""
        if not self.available:
            return
        node_id = f"{entity_type}:{entity_id}"
        self._graph.add_node(
            node_id,
            entity_type=entity_type,
            entity_id=entity_id,
            properties=properties or {},
            created_at=datetime.utcnow().isoformat(),
        )
        self._stats["nodes"] = self._graph.number_of_nodes()

    def add_relationship(self, source_id: str, source_type: str,
                         target_id: str, target_type: str,
                         relation: str, properties: Dict = None):
        """Add a directed edge between two entities."""
        if not self.available:
            return
        src = f"{source_type}:{source_id}"
        tgt = f"{target_type}:{target_id}"
        # Auto-create nodes if they don't exist
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

    # ── Alert Ingestion ──────────────────────────────────────────────

    def ingest_alert(self, alert: Dict):
        """
        Ingest a security alert and create all relevant graph relationships.
        This is the primary way alerts feed into the knowledge graph.
        """
        if not self.available:
            return

        alert_id = str(alert.get("id", "unknown"))
        alert_type = alert.get("alert_type", "unknown")
        source_ip = alert.get("source_ip")
        dest_ip = alert.get("dest_ip")
        mitre_id = alert.get("mitre_id")
        severity = alert.get("severity", "medium")
        evidence = alert.get("evidence", {})

        # Add alert node
        self.add_entity(alert_id, "alert", {
            "type": alert_type,
            "severity": severity,
            "title": alert.get("title", ""),
            "confidence": alert.get("confidence", 0),
        })

        # Source IP → triggered → Alert
        if source_ip:
            self.add_entity(source_ip, "ip", {"role": "source"})
            self.add_relationship(source_ip, "ip", alert_id, "alert", "triggered")

        # Alert → targets → Dest IP
        if dest_ip:
            self.add_entity(dest_ip, "ip", {"role": "target"})
            self.add_relationship(alert_id, "alert", dest_ip, "ip", "targets")

        # Alert → maps_to → MITRE Technique
        if mitre_id:
            self.add_entity(mitre_id, "mitre_technique", {
                "tactic": alert.get("mitre_tactic", ""),
                "name": alert.get("mitre_technique_name", ""),
            })
            self.add_relationship(alert_id, "alert", mitre_id, "mitre_technique", "maps_to")

        # Source IP → targets → Dest IP
        if source_ip and dest_ip:
            self.add_relationship(source_ip, "ip", dest_ip, "ip", "communicates_with")

        # Handle usernames from evidence
        target_users = evidence.get("target_users", [])
        username = evidence.get("username")
        if username:
            target_users.append(username)
        for user in target_users:
            self.add_entity(user, "user", {"role": "targeted"})
            self.add_relationship(alert_id, "alert", user, "user", "targets_user")

        # Handle hostnames from evidence
        hostname = evidence.get("hostname")
        if hostname:
            self.add_entity(hostname, "device", {"hostname": hostname})
            self.add_relationship(alert_id, "alert", hostname, "device", "affects_device")

        logger.debug(f"Knowledge graph ingested alert {alert_id}: {self._stats}")

    def ingest_incident(self, incident: Dict):
        """Ingest an incident and link to related alerts."""
        if not self.available:
            return

        incident_id = str(incident.get("id", "unknown"))
        self.add_entity(incident_id, "incident", {
            "title": incident.get("title", ""),
            "severity": incident.get("severity", "medium"),
            "status": incident.get("status", "open"),
        })

        # Link related alerts
        for alert_id in (incident.get("related_alert_ids") or []):
            self.add_relationship(
                str(alert_id), "alert",
                incident_id, "incident",
                "escalated_to"
            )

    def seed_demo_data(self):
        """Seed the graph with complex threat intelligence relationships for the demo."""
        if not self.available or self._stats["nodes"] > 100:
            return # Already seeded or unavailable
        
        logger.info("🌱 Seeding Security Knowledge Graph with Threat Intelligence data...")
        
        # APT Groups
        self.add_entity("APT29", "threat_actor", {"name": "Cozy Bear", "origin": "Russia"})
        self.add_entity("Lazarus", "threat_actor", {"name": "Lazarus Group", "origin": "North Korea"})
        
        # Malware Families
        self.add_entity("WannaCry", "malware", {"type": "Ransomware"})
        self.add_entity("Emotet", "malware", {"type": "Botnet/Trojan"})
        self.add_entity("CobaltStrike", "malware", {"type": "C2 Framework"})
        
        # Vulnerabilities
        self.add_entity("CVE-2021-44228", "cve", {"name": "Log4Shell", "cvss": 10.0})
        self.add_entity("CVE-2023-34362", "cve", {"name": "MOVEit RCE", "cvss": 9.8})
        
        # Assets
        self.add_entity("prod-db-01", "asset", {"criticality": "high", "os": "Linux"})
        self.add_entity("hr-fileshare", "asset", {"criticality": "medium", "os": "Windows"})
        
        # Users
        self.add_entity("alice.smith", "user", {"role": "Admin", "department": "IT"})
        self.add_entity("bob.jones", "user", {"role": "User", "department": "HR"})
        
        # MITRE Techniques
        self.add_entity("T1110", "mitre_technique", {"name": "Brute Force"})
        self.add_entity("T1190", "mitre_technique", {"name": "Exploit Public-Facing App"})
        self.add_entity("T1486", "mitre_technique", {"name": "Data Encrypted for Impact"})
        
        # --- Create Relationships ---
        
        # Threat Actors -> Malware
        self.add_relationship("Lazarus", "threat_actor", "WannaCry", "malware", "uses")
        self.add_relationship("APT29", "threat_actor", "CobaltStrike", "malware", "uses")
        
        # Threat Actors -> CVEs
        self.add_relationship("Lazarus", "threat_actor", "CVE-2021-44228", "cve", "exploits")
        
        # Malware -> MITRE
        self.add_relationship("WannaCry", "malware", "T1486", "mitre_technique", "implements")
        self.add_relationship("CobaltStrike", "malware", "T1190", "mitre_technique", "implements")
        
        # Vulnerabilities -> Assets
        self.add_relationship("prod-db-01", "asset", "CVE-2021-44228", "cve", "vulnerable_to")
        self.add_relationship("hr-fileshare", "asset", "CVE-2023-34362", "cve", "vulnerable_to")
        
        # Users -> Assets
        self.add_relationship("alice.smith", "user", "prod-db-01", "asset", "administers")
        self.add_relationship("bob.jones", "user", "hr-fileshare", "asset", "accesses")
        
        # Link existing alerts to this web if possible
        # We will add a demo incident to tie it all together
        self.add_entity("INC-999", "incident", {"title": "Ransomware Outbreak on HR Share", "severity": "critical"})
        self.add_relationship("INC-999", "incident", "WannaCry", "malware", "involves")
        self.add_relationship("INC-999", "incident", "hr-fileshare", "asset", "affects")
        self.add_relationship("INC-999", "incident", "Lazarus", "threat_actor", "attributed_to")

    # ── Queries ──────────────────────────────────────────────────────

    def get_entity_context(self, entity_id: str, entity_type: str, max_depth: int = 2) -> Dict:
        """
        Get the full context of an entity — all connected nodes up to max_depth.
        Used by investigation agent for attack path reconstruction.
        """
        if not self.available:
            return {"entity": f"{entity_type}:{entity_id}", "related": [], "paths": []}

        self._stats["queries"] += 1
        node = f"{entity_type}:{entity_id}"

        if node not in self._graph:
            return {"entity": node, "related": [], "paths": []}

        # BFS to find all connected entities within depth
        related = []
        visited = {node}
        queue = [(node, 0)]

        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            # Outgoing edges
            for _, neighbor, data in self._graph.out_edges(current, data=True):
                if neighbor not in visited:
                    visited.add(neighbor)
                    neighbor_data = self._graph.nodes[neighbor]
                    related.append({
                        "entity": neighbor,
                        "type": neighbor_data.get("entity_type", "unknown"),
                        "relation": data.get("relation", "connected"),
                        "direction": "outgoing",
                        "depth": depth + 1,
                        "properties": neighbor_data.get("properties", {}),
                    })
                    queue.append((neighbor, depth + 1))

            # Incoming edges
            for predecessor, _, data in self._graph.in_edges(current, data=True):
                if predecessor not in visited:
                    visited.add(predecessor)
                    pred_data = self._graph.nodes[predecessor]
                    related.append({
                        "entity": predecessor,
                        "type": pred_data.get("entity_type", "unknown"),
                        "relation": data.get("relation", "connected"),
                        "direction": "incoming",
                        "depth": depth + 1,
                        "properties": pred_data.get("properties", {}),
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
        
        alerts = [r for r in context.get("related", []) if r["type"] == "alert"]
        techniques = [r for r in context.get("related", []) if r["type"] == "mitre_technique"]
        users_targeted = [r for r in context.get("related", []) if r["type"] == "user"]
        devices = [r for r in context.get("related", []) if r["type"] == "device"]

        return {
            "ip": ip,
            "total_alerts": len(alerts),
            "alerts": alerts,
            "mitre_techniques": [t["entity"].split(":")[1] for t in techniques],
            "users_targeted": [u["entity"].split(":")[1] for u in users_targeted],
            "devices_affected": [d["entity"].split(":")[1] for d in devices],
            "risk_score": min(1.0, len(alerts) * 0.15 + len(techniques) * 0.1),
            "communicates_with": [
                r["entity"].split(":")[1] for r in context.get("related", [])
                if r["type"] == "ip" and r["relation"] == "communicates_with"
            ],
        }

    def get_attack_path(self, source_ip: str, target_ip: str) -> List[Dict]:
        """Find attack paths between source and target IPs."""
        if not self.available:
            return []

        src = f"ip:{source_ip}"
        tgt = f"ip:{target_ip}"

        if src not in self._graph or tgt not in self._graph:
            return []

        try:
            paths = list(nx.all_simple_paths(self._graph, src, tgt, cutoff=5))
            result = []
            for path in paths[:3]:  # Max 3 paths
                path_detail = []
                for i in range(len(path) - 1):
                    edge_data = self._graph.get_edge_data(path[i], path[i + 1]) or {}
                    path_detail.append({
                        "from": path[i],
                        "to": path[i + 1],
                        "relation": edge_data.get("relation", "connected"),
                    })
                result.append({"path": path, "edges": path_detail, "length": len(path)})
            return result
        except nx.NetworkXError:
            return []

    def get_graph_stats(self) -> Dict:
        """Get knowledge graph statistics."""
        if not self.available:
            return {"available": False, "reason": "networkx not installed"}

        # Count by type
        type_counts = defaultdict(int)
        for _, data in self._graph.nodes(data=True):
            type_counts[data.get("entity_type", "unknown")] += 1

        relation_counts = defaultdict(int)
        for _, _, data in self._graph.edges(data=True):
            relation_counts[data.get("relation", "unknown")] += 1

        return {
            "available": True,
            "total_nodes": self._graph.number_of_nodes(),
            "total_edges": self._graph.number_of_edges(),
            "node_types": dict(type_counts),
            "relationship_types": dict(relation_counts),
            "queries_served": self._stats["queries"],
        }

    def get_graph_visualization_data(self) -> Dict:
        """Export graph data for frontend visualization."""
        if not self.available:
            return {"nodes": [], "edges": []}

        nodes = []
        for node_id, data in self._graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "type": data.get("entity_type", "unknown"),
                "label": data.get("entity_id", node_id),
                "properties": data.get("properties", {}),
            })

        edges = []
        for src, tgt, data in self._graph.edges(data=True):
            edges.append({
                "source": src,
                "target": tgt,
                "relation": data.get("relation", "connected"),
            })

        return {"nodes": nodes, "edges": edges}


# ── Singleton ────────────────────────────────────────────────────────

_kg_instance: Optional[SecurityKnowledgeGraph] = None


def get_knowledge_graph() -> SecurityKnowledgeGraph:
    """Get the singleton knowledge graph instance."""
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = SecurityKnowledgeGraph()
        logger.info(f"✅ Knowledge graph initialized (networkx available: {HAS_NETWORKX})")
    return _kg_instance
