"""
SecureFlow AI - Agentic RAG Router (Section 7 - PART 4)
Specialized retrieval agents for different security domains.
Routes queries to the most relevant knowledge sources.

Agents:
  - ThreatIntelRetrievalAgent    → MITRE, CISA KEV, CVE, IOCs
  - ComplianceRetrievalAgent     → NIST, CIS, OWASP, ISO27001
  - VulnerabilityRetrievalAgent  → CVE, KEV, SANS advisories
  - IncidentHistoryAgent         → Past incidents, playbooks, lessons learned
  - PlaybookRetrievalAgent       → Response playbooks, runbooks
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


# ─── Query Classification Patterns ────────────────────────────────────────────

AGENT_ROUTING_RULES = {
    "threat_intel": {
        "keywords": [
            "mitre", "att&ck", "threat actor", "apt", "campaign", "technique", "tactic",
            "malware", "ransomware", "ioc", "indicator", "c2", "command and control",
            "lazarus", "fancy bear", "cozy bear", "fin7", "carbanak", "darkside",
            "attack pattern", "ttp", "kill chain", "lateral movement",
        ],
        "patterns": [r"T\d{4}(\.\d{3})?", r"APT\d+", r"TA\d+"],
        "priority_sources": ["mitre", "sans", "cisa_kev"],
    },
    "compliance": {
        "keywords": [
            "nist", "cis", "iso", "soc2", "pci", "gdpr", "hipaa", "compliance",
            "control", "framework", "audit", "regulatory", "policy", "standard",
            "requirement", "assessment", "gap analysis",
        ],
        "patterns": [r"NIST SP \d{3}", r"CIS Control \d+", r"ISO \d{5}"],
        "priority_sources": ["nist", "cis", "owasp"],
    },
    "vulnerability": {
        "keywords": [
            "cve", "vulnerability", "exploit", "patch", "cvss", "cwe", "advisory",
            "zero-day", "0day", "poc", "proof of concept", "affected version",
            "log4shell", "log4j", "eternalblue", "printnightmare", "follina",
        ],
        "patterns": [r"CVE-\d{4}-\d{4,7}", r"CWE-\d+", r"CVSS\s+\d+\.\d+"],
        "priority_sources": ["cve", "cisa_kev"],
    },
    "incident": {
        "keywords": [
            "incident", "breach", "attack", "intrusion", "alert", "investigation",
            "timeline", "forensics", "evidence", "chain of custody", "triage",
            "blast radius", "affected systems", "containment",
        ],
        "patterns": [],
        "priority_sources": ["playbooks", "mitre"],
    },
    "playbook": {
        "keywords": [
            "playbook", "runbook", "procedure", "response", "how to", "step", "guide",
            "remediate", "fix", "resolve", "containment", "eradication", "recovery",
        ],
        "patterns": [],
        "priority_sources": ["playbooks", "sans", "nist"],
    },
    "owasp_llm": {
        "keywords": [
            "llm", "ai security", "prompt injection", "jailbreak", "hallucination",
            "sensitive disclosure", "excessive agency", "training data", "rag security",
            "owasp llm", "ai safety",
        ],
        "patterns": [r"LLM\d{2}", r"OWASP LLM"],
        "priority_sources": ["owasp_llm", "owasp"],
    },
}


class AgenticRAGRouter:
    """
    Routes security queries to specialized retrieval agents.
    Each agent knows which knowledge sources to prioritize.
    
    Routing logic:
    1. Classify query intent using keyword + pattern matching
    2. Select primary retrieval agent
    3. Decompose complex queries into sub-queries
    4. Merge and re-rank results from multiple agents
    5. Assemble final context for LLM generation
    """

    def __init__(self):
        self.query_cache: Dict[str, Dict] = {}
        self._stats = {
            "total_queries": 0,
            "threat_intel": 0,
            "compliance": 0,
            "vulnerability": 0,
            "incident": 0,
            "playbook": 0,
            "owasp_llm": 0,
            "general": 0,
        }

    def classify_query(self, query: str) -> Tuple[str, float, List[str]]:
        """
        Classify query into a retrieval domain.
        Returns: (domain, confidence, matched_sources)
        """
        query_lower = query.lower()
        scores: Dict[str, float] = {}

        for domain, rules in AGENT_ROUTING_RULES.items():
            score = 0.0

            # Keyword matching
            for kw in rules["keywords"]:
                if kw in query_lower:
                    score += 1.0

            # Pattern matching (higher weight)
            for pattern in rules["patterns"]:
                if re.search(pattern, query, re.IGNORECASE):
                    score += 3.0

            if score > 0:
                scores[domain] = score

        if not scores:
            return "general", 0.5, ["mitre", "nist", "owasp", "sans"]

        best_domain = max(scores, key=scores.get)
        max_score = scores[best_domain]
        total_score = sum(scores.values())
        confidence = min(max_score / total_score if total_score > 0 else 0.5, 1.0)

        sources = AGENT_ROUTING_RULES[best_domain]["priority_sources"]
        return best_domain, round(confidence, 2), sources

    def decompose_query(self, query: str, domain: str) -> List[str]:
        """
        Decompose a complex query into focused sub-queries.
        """
        sub_queries = [query]  # Always include original

        # Add domain-specific expansions
        if domain == "threat_intel":
            # Extract technique IDs
            techniques = re.findall(r"T\d{4}(?:\.\d{3})?", query, re.IGNORECASE)
            for t in techniques:
                sub_queries.append(f"MITRE ATT&CK {t} technique description and detections")

            # Extract CVEs
            cves = re.findall(r"CVE-\d{4}-\d{4,7}", query, re.IGNORECASE)
            for cve in cves:
                sub_queries.append(f"{cve} vulnerability details exploitation")

        elif domain == "compliance":
            # Add framework-specific queries
            if "nist" in query.lower():
                sub_queries.append("NIST CSF identify protect detect respond recover controls")
            if "cis" in query.lower():
                sub_queries.append("CIS controls implementation groups safeguards")

        elif domain == "playbook":
            # Add response step queries
            query_lower = query.lower()
            if "ransomware" in query_lower:
                sub_queries.append("ransomware containment isolation steps")
                sub_queries.append("ransomware recovery eradication procedure")
            elif "brute force" in query_lower:
                sub_queries.append("brute force account lockout remediation")
            elif "phishing" in query_lower:
                sub_queries.append("phishing email investigation quarantine steps")

        return list(dict.fromkeys(sub_queries))[:5]  # Deduplicate, max 5

    def route_and_retrieve(self, query: str, top_k: int = 8) -> Dict[str, Any]:
        """
        Main routing function. Classifies, decomposes, retrieves, and merges.
        """
        start_time = time.time()
        self._stats["total_queries"] += 1

        # Classify
        domain, confidence, priority_sources = self.classify_query(query)
        self._stats[domain] = self._stats.get(domain, 0) + 1

        # Decompose
        sub_queries = self.decompose_query(query, domain)

        # Retrieve using RAG engine
        try:
            from app.knowledge.rag_engine import get_rag_engine
            engine = get_rag_engine()

            all_results = []
            seen_ids = set()

            # Primary query with source filter
            for source in priority_sources[:2]:  # Top 2 priority sources
                try:
                    results = engine.search(query, top_k=top_k // 2, source_filter=source)
                    for r in results:
                        doc_id = r.get("id") or r.get("title", "")[:50]
                        if doc_id not in seen_ids:
                            r["retrieval_source_filter"] = source
                            all_results.append(r)
                            seen_ids.add(doc_id)
                except Exception:
                    pass

            # General search to fill remaining slots
            general_results = engine.search(query, top_k=top_k)
            for r in general_results:
                doc_id = r.get("id") or r.get("title", "")[:50]
                if doc_id not in seen_ids and len(all_results) < top_k:
                    all_results.append(r)
                    seen_ids.add(doc_id)

        except Exception as e:
            logger.warning(f"RAG engine unavailable: {e}")
            all_results = []

        result = {
            "query": query,
            "domain": domain,
            "agent": f"{domain}_retrieval_agent",
            "confidence": confidence,
            "priority_sources": priority_sources,
            "sub_queries": sub_queries,
            "results": all_results[:top_k],
            "result_count": len(all_results[:top_k]),
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "timestamp": datetime.utcnow().isoformat(),
        }

        return result

    def assemble_context(self, retrieval_result: Dict[str, Any], max_tokens: int = 4000) -> str:
        """
        Assemble retrieved documents into LLM-ready context.
        Handles deduplication, ranking, and token budget management.
        """
        results = retrieval_result.get("results", [])
        domain = retrieval_result.get("domain", "general")
        query = retrieval_result.get("query", "")

        context_parts = [
            f"## Retrieved Security Knowledge",
            f"Query Domain: {domain.replace('_', ' ').title()}",
            f"Sources Retrieved: {len(results)}\n",
        ]

        char_budget = max_tokens * 4  # ~4 chars per token
        used = len("\n".join(context_parts))

        for i, doc in enumerate(results, 1):
            title = doc.get("title") or doc.get("name") or f"Document {i}"
            content = doc.get("content") or doc.get("text") or doc.get("description") or ""
            source = doc.get("source") or doc.get("metadata", {}).get("source", "unknown")
            score = doc.get("score", 0)

            doc_text = f"### [{i}] {title}\n**Source:** {source} | **Relevance:** {score:.3f}\n{content[:800]}\n"

            if used + len(doc_text) > char_budget:
                context_parts.append(f"[{len(results) - i + 1} additional results truncated for token limit]")
                break

            context_parts.append(doc_text)
            used += len(doc_text)

        return "\n".join(context_parts)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "router_stats": self._stats,
            "routing_rules": list(AGENT_ROUTING_RULES.keys()),
        }


# ─── Singleton ────────────────────────────────────────────────────────────────

_router_instance: Optional[AgenticRAGRouter] = None


def get_agentic_router() -> AgenticRAGRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = AgenticRAGRouter()
    return _router_instance
