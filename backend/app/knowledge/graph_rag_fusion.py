"""
SecureFlow AI — GraphRAG Fusion Engine
Fuses Knowledge Graph context with RAG retrieval into a single enriched context
injected into every AI agent call.

Architecture:
  Query → [GraphRAG Fusion]
              ├─→ Knowledge Graph traversal  (entity relationships, attack paths)
              ├─→ RAG semantic search        (threat intel, compliance docs)
              └─→ Merged & ranked context   → LLM Agent

Benefits:
  - Accuracy: graph relationships ground RAG results in real entity context
  - Explainability: every claim is traceable to a graph edge or document
  - Threat Hunting: lateral movement and blast radius from graph enrich text answers
  - Incident Investigation: related alerts, users, IOCs pulled automatically
"""

import logging
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class GraphRAGFusion:
    """
    Central fusion layer that combines:
      1. Knowledge Graph context (entity neighbours, attack paths, risk scores)
      2. RAG vector search results (threat intel documents, playbooks, CVE advisories)

    Used by all AI agents through the shared `get_fused_context()` method.
    """

    def __init__(self):
        self._stats = {
            "total_fusions": 0,
            "graph_hits": 0,
            "rag_hits": 0,
            "full_fusions": 0,
        }

    def get_fused_context(
        self,
        query: str,
        agent_name: str = "unknown",
        max_graph_entities: int = 8,
        max_rag_results: int = 6,
        include_risk_context: bool = True,
    ) -> str:
        """
        Primary method — returns a single enriched context string for LLM injection.

        The context is structured as:
          ## Security Knowledge Graph Context  (graph relationships)
          ## Threat Intelligence & Knowledge   (RAG documents)
          ## Risk & Threat Summary             (derived insights)
        """
        start = time.time()
        self._stats["total_fusions"] += 1

        sections: List[str] = []

        # ── 1. Knowledge Graph traversal ───────────────────────────────
        graph_ctx = self._get_graph_context(query, max_graph_entities)
        if graph_ctx:
            self._stats["graph_hits"] += 1
            sections.append(graph_ctx)

        # ── 2. RAG semantic search ─────────────────────────────────────
        rag_ctx = self._get_rag_context(query, max_rag_results)
        if rag_ctx:
            self._stats["rag_hits"] += 1
            sections.append(rag_ctx)

        # ── 3. Risk & threat summary ───────────────────────────────────
        if include_risk_context:
            risk_ctx = self._get_risk_summary(query)
            if risk_ctx:
                sections.append(risk_ctx)

        if not sections:
            return ""

        if graph_ctx and rag_ctx:
            self._stats["full_fusions"] += 1

        elapsed_ms = int((time.time() - start) * 1000)
        header = (
            f"<!-- GraphRAG Fusion | agent={agent_name} "
            f"sections={len(sections)} elapsed={elapsed_ms}ms -->\n"
        )

        return header + "\n\n".join(sections)

    def _get_graph_context(self, query: str, max_entities: int) -> str:
        """Pull entity context from the knowledge graph."""
        try:
            from app.knowledge.knowledge_graph import get_knowledge_graph
            kg = get_knowledge_graph()
            if not kg.available:
                return ""
            return kg.get_graph_context_for_query(query, max_entities=max_entities)
        except Exception as e:
            logger.debug(f"GraphRAG graph context failed: {e}")
            return ""

    def _get_rag_context(self, query: str, max_results: int) -> str:
        """Pull relevant documents from the RAG engine."""
        try:
            from app.knowledge.rag_engine import get_rag_engine
            engine = get_rag_engine()
            results = engine.search(query, top_k=max_results)
            if not results:
                return ""

            lines = ["## Threat Intelligence & Security Knowledge"]
            for i, doc in enumerate(results[:max_results], 1):
                title   = doc.get("title") or doc.get("name") or f"Document {i}"
                content = doc.get("content") or doc.get("text") or doc.get("description") or ""
                source  = doc.get("source") or doc.get("metadata", {}).get("source", "kb")
                score   = doc.get("score", 0)
                lines.append(
                    f"\n### [{i}] {title}\n"
                    f"**Source:** {source} | **Relevance:** {score:.3f}\n"
                    f"{content[:600]}"
                )
            return "\n".join(lines)
        except Exception as e:
            logger.debug(f"GraphRAG RAG context failed: {e}")
            return ""

    def _get_risk_summary(self, query: str) -> str:
        """Generate a risk-aware summary using graph hunting queries."""
        try:
            from app.knowledge.knowledge_graph import get_knowledge_graph
            kg = get_knowledge_graph()
            if not kg.available:
                return ""

            lines = []
            query_lower = query.lower()

            # Lateral movement
            if any(kw in query_lower for kw in ["lateral", "movement", "pivot", "spread", "incident"]):
                chains = kg.hunt_lateral_movement()
                if chains:
                    lines.append("## Active Lateral Movement Chains Detected")
                    for c in chains[:4]:
                        lines.append(f"  ⚠ {c['from_entity']} → [{c['from_type']}] → {c['to_entity']} [{c['to_type']}]")

            # Malicious IPs
            if any(kw in query_lower for kw in ["malicious", "ip", "ioc", "indicator", "c2", "command"]):
                hits = kg.hunt_devices_with_malicious_ips()
                if hits:
                    lines.append("## Devices/Assets Communicating with Malicious IPs")
                    for h in hits[:4]:
                        lines.append(f"  🔴 {h['entity']} ↔ {h['malicious_ioc']} via [{h['relation']}]")

            # Vulnerable assets
            if any(kw in query_lower for kw in ["cve", "vulnerability", "vuln", "patch", "exploit"]):
                vulns = kg.hunt_vulnerable_connected_assets()
                if vulns:
                    lines.append("## Vulnerable Assets Connected to Critical Infrastructure")
                    for v in vulns[:4]:
                        cve_str = ", ".join(v["cves"][:3])
                        lines.append(f"  🟠 {v['entity']} vulnerable to {cve_str}, connected to {len(v['connected_assets'])} assets")

            # MITRE coverage
            if any(kw in query_lower for kw in ["mitre", "technique", "tactic", "control", "coverage"]):
                cov = kg.get_mitre_coverage()
                if cov:
                    lines.append(
                        f"## MITRE ATT&CK Coverage\n"
                        f"  Techniques in use by threat actors: {cov['total_techniques']}\n"
                        f"  Covered by security controls: {cov['covered']} ({cov['coverage_pct']}%)\n"
                        f"  Uncovered techniques: {', '.join(cov['uncovered_techniques'][:5])}"
                    )

            return "\n".join(lines) if lines else ""
        except Exception as e:
            logger.debug(f"GraphRAG risk summary failed: {e}")
            return ""

    def get_blast_radius(self, entity_id: str, entity_type: str) -> Dict[str, Any]:
        """Get full blast radius for a compromised entity."""
        try:
            from app.knowledge.knowledge_graph import get_knowledge_graph
            kg = get_knowledge_graph()
            return kg.propagate_risk(entity_id, entity_type)
        except Exception as e:
            logger.warning(f"Blast radius computation failed: {e}")
            return {}

    def get_attack_path(self, src_id: str, src_type: str, tgt_id: str, tgt_type: str) -> List[Dict]:
        """Get attack paths between two entities."""
        try:
            from app.knowledge.knowledge_graph import get_knowledge_graph
            kg = get_knowledge_graph()
            return kg.get_attack_path(src_id, src_type, tgt_id, tgt_type)
        except Exception as e:
            logger.warning(f"Attack path computation failed: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        return self._stats


# ── Singleton ────────────────────────────────────────────────────────────────

_fusion_instance: Optional[GraphRAGFusion] = None


def get_graph_rag_fusion() -> GraphRAGFusion:
    global _fusion_instance
    if _fusion_instance is None:
        _fusion_instance = GraphRAGFusion()
        logger.info("✅ GraphRAG Fusion engine initialized")
    return _fusion_instance
