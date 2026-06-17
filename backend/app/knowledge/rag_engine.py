"""
SecureFlow AI — Advanced RAG Engine
Uses ChromaDB for vector storage, SentenceTransformers for semantic embeddings,
and rank_bm25 for keyword search. Implements reciprocal rank fusion for hybrid search.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    from rank_bm25 import BM25Okapi
    HAS_RAG_DEPS = True
except ImportError:
    HAS_RAG_DEPS = False
    logger.warning("RAG dependencies missing. Install chromadb, sentence-transformers, rank_bm25")


class AdvancedRAGEngine:
    """Production-grade RAG engine for SecureFlow AI."""

    def __init__(self, knowledge_dir: str = None):
        if not HAS_RAG_DEPS:
            raise RuntimeError("RAG dependencies not installed.")
            
        if knowledge_dir is None:
            from app.config import settings
            knowledge_dir = settings.KNOWLEDGE_DIR
            
        self._knowledge_dir = knowledge_dir
        self._loaded = False
        
        # Initialize Embedding Model
        logger.info("Loading embedding model (all-MiniLM-L6-v2)...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB (In-memory for hackathon, can use PersistentClient)
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection(
            name="secureflow_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Store for BM25 keyword search
        self._raw_docs = []
        self._bm25 = None
        self._doc_ids = []

    def load(self):
        """Load and index all knowledge sources."""
        if self._loaded:
            return

        files = {
            "mitre": "mitre_knowledge.json",
            "owasp": "owasp_knowledge.json",
            "cis": "cis_knowledge.json",
            "nist": "nist_knowledge.json",
            "cve": "cve_knowledge.json",
            "playbooks": "playbooks.json",
        }

        docs_to_add = []
        metadatas = []
        ids = []
        
        for source, filename in files.items():
            path = os.path.join(self._knowledge_dir, filename)
            if not os.path.exists(path):
                logger.warning(f"File not found: {path}")
                continue
                
            try:
                with open(path, "r", encoding="utf-8") as f:
                    items = json.load(f)
                    
                for i, item in enumerate(items):
                    doc_id = f"{source}-{item.get('id', i)}"
                    
                    # Create search text
                    text_parts = [
                        str(item.get("name", item.get("control", item.get("id", "")))),
                        str(item.get("description", "")),
                        str(item.get("detection", "")),
                        str(item.get("remediation", item.get("implementation", "")))
                    ]
                    search_text = " ".join([p for p in text_parts if p]).lower()
                    
                    # Metadata for filtering
                    meta = {
                        "source": source,
                        "id": item.get("id", str(i)),
                        "title": item.get("name", item.get("control", "Untitled")),
                        "original_json": json.dumps(item)
                    }
                    
                    docs_to_add.append(search_text)
                    metadatas.append(meta)
                    ids.append(doc_id)
                    
                    # Save for BM25
                    self._raw_docs.append(item)
                    self._doc_ids.append(doc_id)
                    
                logger.info(f"Loaded {len(items)} items from {source}")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")

        # Index in ChromaDB
        if docs_to_add:
            logger.info("Generating embeddings and indexing in ChromaDB...")
            embeddings = self.encoder.encode(docs_to_add).tolist()
            self.collection.add(
                documents=docs_to_add,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            # Setup BM25
            tokenized_corpus = [doc.split(" ") for doc in docs_to_add]
            self._bm25 = BM25Okapi(tokenized_corpus)
            
        self._loaded = True
        logger.info(f"✅ RAG Engine loaded: {self.collection.count()} documents indexed")

    def search(self, query: str, top_k: int = 3, source_filter: str = None) -> List[Dict]:
        """Hybrid search combining Semantic Search and BM25."""
        if not self._loaded:
            self.load()
            
        if self.collection.count() == 0:
            return []

        # 1. Semantic Search
        query_embedding = self.encoder.encode(query).tolist()
        where_clause = {"source": source_filter} if source_filter else None
        
        semantic_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,
            where=where_clause
        )
        
        # 2. Keyword Search (BM25)
        tokenized_query = query.lower().split(" ")
        bm25_scores = self._bm25.get_scores(tokenized_query)
        
        # Combine scores using Reciprocal Rank Fusion (RRF)
        # RRF = 1 / (k + rank)
        combined_scores = {}
        k = 60
        
        # Add semantic ranks
        if semantic_results and semantic_results["ids"]:
            for i, doc_id in enumerate(semantic_results["ids"][0]):
                rank = i + 1
                combined_scores[doc_id] = {
                    "rrf": 1.0 / (k + rank), 
                    "meta": semantic_results["metadatas"][0][i]
                }
                
        # Add BM25 ranks
        top_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k*2]
        
        for rank_idx, idx in enumerate(top_bm25_indices):
            if bm25_scores[idx] <= 0:
                continue
            
            doc_id = self._doc_ids[idx]
            rrf_score = 1.0 / (k + rank_idx + 1)
            
            # Boost exact substring matches in ID or title heavily
            meta = None
            if doc_id in combined_scores:
                meta = combined_scores[doc_id]["meta"]
            else:
                for i, r_id in enumerate(self._doc_ids):
                    if r_id == doc_id:
                        meta = {"source": "unknown", "original_json": json.dumps(self._raw_docs[i])}
                        break
            
            if meta:
                # Apply source filter
                if doc_id in combined_scores:
                    combined_scores[doc_id]["rrf"] += rrf_score
                else:
                    combined_scores[doc_id] = {"rrf": rrf_score, "meta": meta}

        # 3. Exact Keyword Match Override (Guarantees IDs/Titles bubble to top)
        query_lower = query.lower()
        for i, item in enumerate(self._raw_docs):
            doc_id = self._doc_ids[i]
            
            # Extract title and ID for matching
            title_match = str(item.get("name", item.get("title", item.get("control", "")))).lower()
            id_match = str(item.get("id", "")).lower()
            
            # If exact match found
            if query_lower in title_match or query_lower in id_match:
                # Check source filter
                source = "unknown"
                if "-" in doc_id:
                    source = doc_id.split("-")[0]
                    
                if source_filter and source != source_filter:
                    continue
                    
                if doc_id in combined_scores:
                    combined_scores[doc_id]["rrf"] += 1.0 # Huge boost
                else:
                    meta = {"source": source, "original_json": json.dumps(item)}
                    combined_scores[doc_id] = {"rrf": 1.0, "meta": meta}

        # Calculate final results
        final_results = []
        for doc_id, scores in combined_scores.items():
            if scores["meta"]:
                try:
                    item_data = json.loads(scores["meta"]["original_json"])
                    final_results.append({
                        "id": doc_id,
                        "source": scores["meta"].get("source", "unknown"),
                        "score": round(scores["rrf"], 3),
                        "data": item_data
                    })
                except Exception:
                    pass

        # Sort and return top_k
        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results[:top_k]

    def get_context_for_prompt(self, query: str, top_k: int = 3) -> str:
        """Get formatted knowledge context to inject into LLM prompts."""
        results = self.search(query, top_k=top_k)
        if not results:
            return ""

        context_parts = ["[KNOWLEDGE BASE CONTEXT (Hybrid Search)]"]
        for r in results:
            data = r["data"]
            source = r["source"].upper()
            
            if r["source"] == "mitre":
                context_parts.append(
                    f"- [{source}] {data.get('id', '')} {data.get('name', '')}: "
                    f"{data.get('description', '')[:250]}... | "
                    f"Detection: {data.get('detection', '')[:150]} | "
                    f"Remediation: {data.get('remediation', '')[:150]}"
                )
            elif r["source"] == "cve":
                context_parts.append(
                    f"- [{source}] {data.get('id', '')} ({data.get('name', '')}): "
                    f"CVSS: {data.get('cvss')} | CISA KEV: {data.get('cisa_kev')} | "
                    f"{data.get('description', '')[:250]}..."
                )
            elif r["source"] in ["cis", "nist"]:
                context_parts.append(
                    f"- [{source}] {data.get('id', data.get('control', ''))}: "
                    f"{data.get('description', '')[:250]}... | "
                    f"Implementation: {data.get('implementation', '')[:150]}"
                )
            elif r["source"] == "playbooks":
                steps = data.get("steps", [])
                context_parts.append(
                    f"- [{source}] {data.get('name', '')}: {data.get('trigger', '')} | "
                    f"Steps: {'; '.join(steps[:4])}"
                )

        return "\n".join(context_parts)

    def stats(self) -> Dict:
        return {
            "loaded": self._loaded,
            "total_documents": self.collection.count() if self._loaded else 0,
            "embedding_model": "all-MiniLM-L6-v2",
            "vector_store": "ChromaDB",
            "hybrid_search": True
        }


# Singleton instance
_rag_instance = None

def get_rag_engine() -> AdvancedRAGEngine:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = AdvancedRAGEngine()
        _rag_instance.load()
    return _rag_instance
