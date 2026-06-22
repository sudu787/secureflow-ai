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
def get_recent_memories(limit: int = 10):
    """Fetch the latest consolidated incident memories."""
    from app.knowledge.incident_memory import get_all_memories
    mems = get_all_memories()
    return mems[:limit]

@router.get("/search")
def search_memory(q: str):
    """Semantic search through past memories using the TF-IDF engine."""
    from app.knowledge.incident_memory import recall_similar_incidents
    results = recall_similar_incidents(query=q, top_k=5)
    return {"results": results}

@router.get("/all")
def get_all():
    """Get all seeded memories for the Memory Center."""
    from app.knowledge.incident_memory import get_all_memories
    return {"memories": get_all_memories()}
