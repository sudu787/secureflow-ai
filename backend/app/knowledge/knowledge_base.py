"""
SecureFlow AI — Knowledge Base & RAG Engine
Retrieval-Augmented Generation using keyword + TF-IDF matching.
Loads MITRE ATT&CK, OWASP, CIS Benchmarks, and security playbooks.
"""

import os
import json
import math
import logging
from collections import defaultdict
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """In-memory knowledge retrieval engine for RAG-enhanced LLM calls."""

    def __init__(self, knowledge_dir: str = None):
        if knowledge_dir is None:
            from app.config import settings
            knowledge_dir = settings.KNOWLEDGE_DIR

        self._documents: List[Dict] = []
        self._idf: Dict[str, float] = {}
        self._doc_vectors: List[Dict[str, float]] = []
        self._loaded = False
        self._knowledge_dir = knowledge_dir

    # ── Loading ──────────────────────────────────────────────────────

    def load(self):
        """Load all knowledge documents from JSON files."""
        if self._loaded:
            return

        files = {
            "mitre": "mitre_knowledge.json",
            "owasp": "owasp_knowledge.json",
            "cis": "cis_knowledge.json",
            "playbooks": "playbooks.json",
        }

        for source, filename in files.items():
            path = os.path.join(self._knowledge_dir, filename)
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        items = json.load(f)
                    for item in items:
                        text = self._item_to_text(item, source)
                        self._documents.append({
                            "source": source,
                            "id": item.get("id", ""),
                            "name": item.get("name", item.get("control", "")),
                            "text": text,
                            "data": item,
                        })
                    logger.info(f"Loaded {len(items)} {source} knowledge items from {filename}")
                except Exception as e:
                    logger.warning(f"Failed to load {filename}: {e}")

        # Build TF-IDF index
        self._build_index()
        self._loaded = True
        logger.info(f"✅ Knowledge base loaded: {len(self._documents)} documents indexed")

    def _item_to_text(self, item: dict, source: str) -> str:
        """Convert a knowledge item to searchable text."""
        parts = []
        for key in ["id", "name", "control", "tactic", "description",
                     "detection", "remediation", "implementation",
                     "trigger", "examples", "mitigation", "steps",
                     "mitre_techniques", "platform"]:
            val = item.get(key)
            if val:
                if isinstance(val, list):
                    parts.append(" ".join(str(v) for v in val))
                else:
                    parts.append(str(val))
        return " ".join(parts).lower()

    def _build_index(self):
        """Build TF-IDF vectors for all documents."""
        n = len(self._documents)
        if n == 0:
            return

        # Document frequency
        df = defaultdict(int)
        doc_tf = []

        for doc in self._documents:
            words = doc["text"].split()
            tf = defaultdict(int)
            for w in words:
                tf[w] += 1
            # Normalize TF
            max_tf = max(tf.values()) if tf else 1
            tf = {w: count / max_tf for w, count in tf.items()}
            doc_tf.append(tf)
            for w in set(words):
                df[w] += 1

        # IDF
        self._idf = {w: math.log(n / (1 + count)) for w, count in df.items()}

        # TF-IDF vectors
        self._doc_vectors = []
        for tf in doc_tf:
            vec = {w: tf_val * self._idf.get(w, 0) for w, tf_val in tf.items()}
            self._doc_vectors.append(vec)

    # ── Retrieval ────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 3, source_filter: str = None) -> List[Dict]:
        """
        Retrieve the top-k most relevant knowledge items for a query.

        Args:
            query: Search query (natural language or keywords)
            top_k: Number of results to return
            source_filter: Optional filter by source (mitre, owasp, cis, playbooks)

        Returns:
            List of knowledge items with relevance scores
        """
        if not self._loaded:
            self.load()

        if not self._documents:
            return []

        query_words = query.lower().split()
        query_tf = defaultdict(int)
        for w in query_words:
            query_tf[w] += 1
        max_qtf = max(query_tf.values()) if query_tf else 1
        query_vec = {
            w: (count / max_qtf) * self._idf.get(w, 0)
            for w, count in query_tf.items()
        }

        # Score each document
        scores = []
        for i, (doc, doc_vec) in enumerate(zip(self._documents, self._doc_vectors)):
            if source_filter and doc["source"] != source_filter:
                continue

            # Cosine similarity
            dot = sum(query_vec.get(w, 0) * doc_vec.get(w, 0) for w in query_vec)
            mag_q = math.sqrt(sum(v ** 2 for v in query_vec.values())) or 1
            mag_d = math.sqrt(sum(v ** 2 for v in doc_vec.values())) or 1
            cosine = dot / (mag_q * mag_d)

            # Boost for exact ID matches (e.g., "T1110")
            id_boost = 0
            for w in query_words:
                if w.upper() == doc["id"].upper():
                    id_boost = 0.5

            scores.append((i, cosine + id_boost))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scores[:top_k]:
            if score > 0.01:  # Minimum relevance threshold
                doc = self._documents[idx]
                results.append({
                    "source": doc["source"],
                    "id": doc["id"],
                    "name": doc["name"],
                    "relevance": round(score, 4),
                    "data": doc["data"],
                })

        return results

    def get_context_for_prompt(self, query: str, top_k: int = 3) -> str:
        """
        Get formatted knowledge context to inject into LLM prompts.

        Returns a string ready to be prepended to the LLM prompt.
        """
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return ""

        context_parts = ["[KNOWLEDGE BASE CONTEXT]"]
        for r in results:
            data = r["data"]
            source = r["source"].upper()
            name = r.get("name", r["id"])

            if r["source"] == "mitre":
                context_parts.append(
                    f"- [{source}] {data['id']} {data['name']} ({data.get('tactic', '')}): "
                    f"{data.get('description', '')[:200]} | "
                    f"Detection: {data.get('detection', '')[:150]} | "
                    f"Remediation: {data.get('remediation', '')[:150]}"
                )
            elif r["source"] == "playbooks":
                steps = data.get("steps", [])
                context_parts.append(
                    f"- [{source}] {data.get('name', '')}: {data.get('trigger', '')} | "
                    f"Steps: {'; '.join(steps[:4])} | "
                    f"Escalation: {data.get('escalation', 'N/A')}"
                )
            elif r["source"] == "owasp":
                context_parts.append(
                    f"- [{source}] {data['id']} {data['name']}: {data.get('description', '')[:200]} | "
                    f"Mitigation: {data.get('mitigation', '')[:150]}"
                )
            elif r["source"] == "cis":
                context_parts.append(
                    f"- [{source}] {data.get('control', '')}: {data.get('description', '')[:200]} | "
                    f"Implementation: {data.get('implementation', '')[:150]}"
                )

        return "\n".join(context_parts)

    def lookup_mitre(self, technique_id: str) -> Optional[Dict]:
        """Look up a specific MITRE ATT&CK technique by ID."""
        if not self._loaded:
            self.load()
        for doc in self._documents:
            if doc["source"] == "mitre" and doc["id"].upper() == technique_id.upper():
                return doc["data"]
        return None

    def lookup_playbook(self, trigger_keywords: List[str]) -> Optional[Dict]:
        """Find the best matching playbook for given trigger keywords."""
        results = self.retrieve(" ".join(trigger_keywords), top_k=1, source_filter="playbooks")
        return results[0]["data"] if results else None


# Singleton instance
_kb_instance = None


def get_knowledge_base() -> KnowledgeBase:
    """Get the singleton knowledge base instance."""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
        _kb_instance.load()
    return _kb_instance
