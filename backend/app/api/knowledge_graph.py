"""
SecureFlow AI — Knowledge Graph API
Endpoints for querying the security knowledge graph.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/stats")
async def graph_stats():
    """Get knowledge graph statistics."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    return kg.get_graph_stats()


@router.get("/visualization")
async def graph_visualization():
    """Get graph data for frontend visualization (nodes + edges)."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    return kg.get_graph_visualization_data()


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_context(entity_type: str, entity_id: str, depth: int = 2):
    """Get full context of an entity — all connected nodes."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    return kg.get_entity_context(entity_id, entity_type, max_depth=min(depth, 4))


@router.get("/ip/{ip_address}")
async def get_ip_threat_profile(ip_address: str):
    """Get threat profile for an IP address."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    return kg.get_ip_threat_profile(ip_address)


@router.get("/attack-path")
async def get_attack_path(source_ip: str, target_ip: str):
    """Find attack paths between two IPs."""
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    paths = kg.get_attack_path(source_ip, target_ip)
    return {"source": source_ip, "target": target_ip, "paths": paths}
