"""
SecureFlow AI - Enhanced RAG API (Part 4 Implementation)
Endpoints for the full Advanced RAG & Security Knowledge Engine.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class RAGQuery(BaseModel):
    query: str
    top_k: int = 8
    source_filter: Optional[str] = None


class AgenticQuery(BaseModel):
    query: str
    top_k: int = 10
    include_context: bool = True


class IngestRequest(BaseModel):
    title: str
    content: str
    source: str
    metadata: Optional[dict] = None


# ─── Standard Search ──────────────────────────────────────────────────────────

@router.post("/search")
async def search_knowledge(request: RAGQuery):
    """Hybrid search (semantic + BM25 + RRF) across all knowledge sources."""
    try:
        from app.knowledge.rag_engine import get_rag_engine
        engine = get_rag_engine()
        results = engine.search(
            query=request.query,
            top_k=request.top_k,
            source_filter=request.source_filter,
        )
        return {
            "query": request.query,
            "results": results,
            "count": len(results),
            "search_type": "hybrid_rrf",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Agentic RAG ──────────────────────────────────────────────────────────────

@router.post("/agentic/search")
async def agentic_search(request: AgenticQuery):
    """
    Agentic RAG — intelligently routes query to the best specialized agent.
    Classifies intent, decomposes query, retrieves from priority sources.
    """
    try:
        from app.knowledge.agentic_rag import get_agentic_router
        router_instance = get_agentic_router()
        result = router_instance.route_and_retrieve(request.query, top_k=request.top_k)

        if request.include_context:
            context = router_instance.assemble_context(result)
            result["assembled_context"] = context

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agentic/classify")
async def classify_query(q: str = Query(..., description="Security query to classify")):
    """Classify a query and show which agent would handle it."""
    try:
        from app.knowledge.agentic_rag import get_agentic_router
        router_instance = get_agentic_router()
        domain, confidence, sources = router_instance.classify_query(q)
        sub_queries = router_instance.decompose_query(q, domain)
        return {
            "query": q,
            "classified_domain": domain,
            "routing_agent": f"{domain}_retrieval_agent",
            "confidence": confidence,
            "priority_sources": sources,
            "decomposed_sub_queries": sub_queries,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agentic/stats")
async def get_agentic_stats():
    """Get routing statistics for all specialized agents."""
    try:
        from app.knowledge.agentic_rag import get_agentic_router
        return get_agentic_router().get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── MITRE Explorer ───────────────────────────────────────────────────────────

@router.get("/mitre/techniques")
async def get_mitre_techniques(tactic: Optional[str] = None):
    """Get MITRE ATT&CK techniques, optionally filtered by tactic."""
    try:
        from app.knowledge.rag_engine import get_rag_engine
        engine = get_rag_engine()
        query = f"MITRE ATT&CK technique {tactic}" if tactic else "MITRE ATT&CK techniques list"
        results = engine.search(query, top_k=20, source_filter="mitre")
        return {
            "tactic_filter": tactic,
            "techniques": results,
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mitre/technique/{technique_id}")
async def get_technique_detail(technique_id: str):
    """Get detailed information about a specific MITRE technique."""
    try:
        from app.knowledge.rag_engine import get_rag_engine
        engine = get_rag_engine()
        results = engine.search(technique_id, top_k=5, source_filter="mitre")
        if not results:
            results = engine.search(f"MITRE {technique_id}", top_k=5)
        return {
            "technique_id": technique_id,
            "details": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── CISA KEV ─────────────────────────────────────────────────────────────────

@router.get("/kev")
async def get_kev_catalog(limit: int = 20):
    """Get CISA Known Exploited Vulnerabilities catalog."""
    try:
        from app.knowledge.rag_engine import get_rag_engine
        engine = get_rag_engine()
        results = engine.search("known exploited vulnerability CISA", top_k=limit, source_filter="cisa_kev")
        return {
            "source": "CISA Known Exploited Vulnerabilities (KEV)",
            "total": len(results),
            "vulnerabilities": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kev/lookup/{cve_id}")
async def lookup_kev(cve_id: str):
    """Check if a CVE is in CISA KEV catalog."""
    try:
        from app.knowledge.rag_engine import get_rag_engine
        engine = get_rag_engine()
        results = engine.search(cve_id, top_k=5, source_filter="cisa_kev")
        kev_match = next((r for r in results if cve_id.upper() in str(r).upper()), None)
        return {
            "cve_id": cve_id,
            "in_kev": kev_match is not None,
            "kev_details": kev_match,
            "severity": "CRITICAL - Active exploitation confirmed" if kev_match else "Not in CISA KEV",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Use-Case Investigation Endpoints ─────────────────────────────────────────

@router.post("/investigate/alert")
async def investigate_alert_with_rag(alert_id: int, use_agentic: bool = True):
    """Run RAG-powered investigation for a specific alert."""
    from fastapi import Depends
    from app.database import get_db
    from sqlalchemy.orm import Session

    try:
        from app.database import SessionLocal
        db = SessionLocal()
        from app.models.alert import Alert
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        db.close()

        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        query = f"{alert.title}. MITRE technique {alert.mitre_technique or ''}. {alert.description or ''}"

        if use_agentic:
            from app.knowledge.agentic_rag import get_agentic_router
            router_instance = get_agentic_router()
            result = router_instance.route_and_retrieve(query, top_k=8)
            context = router_instance.assemble_context(result)
            result["assembled_context"] = context
            result["alert_id"] = alert_id
            return result
        else:
            from app.knowledge.rag_engine import get_rag_engine
            engine = get_rag_engine()
            results = engine.search(query, top_k=8)
            return {"alert_id": alert_id, "query": query, "results": results}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
async def get_knowledge_sources():
    """Get all available knowledge sources and their document counts."""
    return {
        "sources": [
            {"id": "mitre", "name": "MITRE ATT&CK Framework", "domain": "Threat Intelligence", "implemented": True},
            {"id": "owasp", "name": "OWASP Top 10", "domain": "Application Security", "implemented": True},
            {"id": "nist", "name": "NIST Cybersecurity Framework", "domain": "Compliance", "implemented": True},
            {"id": "cis", "name": "CIS Controls v8", "domain": "Compliance", "implemented": True},
            {"id": "cve", "name": "CVE Database", "domain": "Vulnerability Intelligence", "implemented": True},
            {"id": "cisa_kev", "name": "CISA Known Exploited Vulnerabilities", "domain": "Vulnerability Intelligence", "implemented": True},
            {"id": "sans", "name": "SANS Security Guidance", "domain": "Security Guidance", "implemented": True},
            {"id": "owasp_llm", "name": "OWASP LLM Top 10", "domain": "AI Security", "implemented": True},
            {"id": "owasp_api", "name": "OWASP API Top 10", "domain": "API Security", "implemented": True},
            {"id": "playbooks", "name": "Security Playbooks", "domain": "Incident Response", "implemented": True},
            {"id": "iso27001", "name": "ISO 27001:2022", "domain": "Compliance", "implemented": False, "roadmap": "Tier 3"},
            {"id": "pci_dss", "name": "PCI DSS v4.0", "domain": "Compliance", "implemented": False, "roadmap": "Tier 3"},
            {"id": "nvd", "name": "NIST NVD Live Feed", "domain": "Vulnerability Intelligence", "implemented": False, "roadmap": "Tier 2"},
        ]
    }


# ─── Stats ────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_rag_stats():
    """Get RAG engine statistics including document counts per source."""
    try:
        from app.knowledge.rag_engine import get_rag_engine
        engine = get_rag_engine()
        stats = engine.stats()

        # Add agentic router stats
        try:
            from app.knowledge.agentic_rag import get_agentic_router
            stats["agentic_router"] = get_agentic_router().get_stats()
        except Exception:
            pass

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
