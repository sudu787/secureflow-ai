"""
SecureFlow AI - Memory API
Endpoints for the Cyber Memory Center.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.memory_service import MemoryService
from app.knowledge.rag_engine import get_rag_engine
from pydantic import BaseModel

router = APIRouter()

class ConsolidateRequest(BaseModel):
    alert_id: int

@router.post("/consolidate")
def consolidate_memory(req: ConsolidateRequest, db: Session = Depends(get_db)):
    """Simulates nightly memory consolidation for a specific alert."""
    memory = MemoryService.consolidate_alert_to_memory(db, req.alert_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    return {
        "status": "success",
        "message": "Memory consolidated and embedded.",
        "memory_id": memory.vector_id,
        "title": memory.title
    }

@router.get("/recent")
def get_recent_memories(limit: int = 10, db: Session = Depends(get_db)):
    """Fetch the latest consolidated incident memories."""
    memories = MemoryService.get_recent_memories(db, limit)
    return [
        {
            "id": m.id,
            "title": m.title,
            "root_cause_summary": m.root_cause_summary,
            "mitigation_applied": m.mitigation_applied,
            "iocs": m.iocs,
            "vector_id": m.vector_id,
            "created_at": m.created_at
        }
        for m in memories
    ]

@router.get("/search")
def search_memory(q: str):
    """Semantic search through past memories using the RAG engine."""
    rag = get_rag_engine()
    results = rag.search(query=q, top_k=5, source_filter="incident_memory")
    return {"results": results}
