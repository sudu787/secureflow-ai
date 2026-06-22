"""
SecureFlow AI — Knowledge Graph API (Full v2)
REST endpoints for the Security Knowledge Graph.
"""

from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()


# ── Core Graph ────────────────────────────────────────────────────────────────

@router.get("/stats")
async def graph_stats():
    """Get knowledge graph statistics (node/edge counts, type breakdown)."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    return kg.get_graph_stats()


@router.get("/visualization")
async def graph_visualization():
    """Get enriched graph data for force-directed visualization (nodes + edges + colors)."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    return kg.get_graph_visualization_data()


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_context(entity_type: str, entity_id: str, depth: int = 2):
    """Get full context of any entity — all connected nodes up to depth."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    return kg.get_entity_context(entity_id, entity_type, max_depth=min(depth, 4))


@router.get("/ip/{ip_address}")
async def get_ip_threat_profile(ip_address: str):
    """Get full threat profile for an IP address (alerts, MITRE, users, IOCs)."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    return kg.get_ip_threat_profile(ip_address)


@router.get("/attack-path")
async def get_attack_path(
    source_id: str = Query(...),
    source_type: str = Query(default="ip"),
    target_id: str = Query(...),
    target_type: str = Query(default="asset"),
):
    """Find all attack paths between any two entities."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    paths = kg.get_attack_path(source_id, source_type, target_id, target_type)
    return {
        "source": f"{source_type}:{source_id}",
        "target": f"{target_type}:{target_id}",
        "paths": paths,
        "path_count": len(paths),
    }


# ── Risk Propagation ─────────────────────────────────────────────────────────

@router.post("/risk/propagate")
async def propagate_risk(body: dict):
    """
    Compute risk propagation blast radius from a compromised entity.

    Body: { "entity_id": "...", "entity_type": "...", "initial_score": 0.9 }
    """
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    entity_id    = body.get("entity_id", "")
    entity_type  = body.get("entity_type", "ip")
    initial_score = float(body.get("initial_score", 0.9))
    return kg.propagate_risk(entity_id, entity_type, initial_score)


@router.get("/risk/propagate/{entity_type}/{entity_id}")
async def propagate_risk_get(entity_type: str, entity_id: str, initial_score: float = 0.9):
    """GET version of risk propagation."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    return kg.propagate_risk(entity_id, entity_type, initial_score)


# ── Threat Hunting ────────────────────────────────────────────────────────────

@router.get("/hunt/lateral-movement")
async def hunt_lateral_movement():
    """Find lateral movement chains in the knowledge graph."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    chains = kg.hunt_lateral_movement()
    return {
        "query": "lateral_movement",
        "results": chains,
        "count": len(chains),
        "threat_level": "critical" if chains else "low",
    }


@router.get("/hunt/malicious-comms")
async def hunt_malicious_communications():
    """Find devices/assets communicating with known malicious IPs/IOCs."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    hits = kg.hunt_devices_with_malicious_ips()
    return {
        "query": "malicious_communications",
        "results": hits,
        "count": len(hits),
        "threat_level": "critical" if any(h["threat"] == "high" for h in hits) else "medium",
    }


@router.get("/hunt/high-risk-users")
async def hunt_high_risk_users():
    """Find users associated with multiple security incidents."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    users = kg.hunt_users_with_multiple_incidents()
    return {
        "query": "high_risk_users",
        "results": users,
        "count": len(users),
    }


@router.get("/hunt/vulnerable-assets")
async def hunt_vulnerable_assets():
    """Find vulnerable assets connected to critical infrastructure."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    vulns = kg.hunt_vulnerable_connected_assets()
    return {
        "query": "vulnerable_connected_assets",
        "results": vulns,
        "count": len(vulns),
        "critical_count": sum(1 for v in vulns if v.get("risk") == "critical"),
    }


@router.get("/hunt/all")
async def run_all_hunts():
    """Run all threat hunting queries and return a consolidated report."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()

    lateral      = kg.hunt_lateral_movement()
    mal_comms    = kg.hunt_devices_with_malicious_ips()
    risky_users  = kg.hunt_users_with_multiple_incidents()
    vuln_assets  = kg.hunt_vulnerable_connected_assets()
    mitre_cov    = kg.get_mitre_coverage()

    total_findings = len(lateral) + len(mal_comms) + len(risky_users) + len(vuln_assets)
    threat_level = "critical" if lateral or mal_comms else "high" if vuln_assets else "medium"

    return {
        "summary": {
            "total_findings": total_findings,
            "threat_level": threat_level,
            "lateral_movement_chains": len(lateral),
            "malicious_communications": len(mal_comms),
            "high_risk_users": len(risky_users),
            "vulnerable_assets": len(vuln_assets),
        },
        "lateral_movement": lateral,
        "malicious_communications": mal_comms,
        "high_risk_users": risky_users,
        "vulnerable_assets": vuln_assets,
        "mitre_coverage": mitre_cov,
    }


# ── MITRE Coverage ────────────────────────────────────────────────────────────

@router.get("/mitre/coverage")
async def get_mitre_coverage():
    """Get MITRE ATT&CK technique coverage by security controls vs. threat actors."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    return kg.get_mitre_coverage()


# ── GraphRAG Fusion ───────────────────────────────────────────────────────────

@router.post("/graphrag/context")
async def get_graphrag_context(body: dict):
    """
    Get GraphRAG fused context for an LLM query.
    Combines graph entity context + RAG document retrieval.

    Body: { "query": "...", "agent_name": "..." }
    """
    from app.knowledge.graph_rag_fusion import get_graph_rag_fusion
    fusion = get_graph_rag_fusion()
    query      = body.get("query", "")
    agent_name = body.get("agent_name", "api")
    ctx = fusion.get_fused_context(query, agent_name=agent_name)
    return {
        "query":   query,
        "context": ctx,
        "fusion_stats": fusion.get_stats(),
    }


@router.get("/graphrag/stats")
async def get_graphrag_stats():
    """Get GraphRAG fusion engine statistics."""
    from app.knowledge.graph_rag_fusion import get_graph_rag_fusion
    fusion = get_graph_rag_fusion()
    return fusion.get_stats()


# ── Seed ─────────────────────────────────────────────────────────────────────

@router.post("/seed")
async def seed_graph():
    """Seed the knowledge graph with demo threat intelligence data."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    kg.seed_demo_data()
    return kg.get_graph_stats()
