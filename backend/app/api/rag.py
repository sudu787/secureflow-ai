from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.knowledge.rag_engine import get_rag_engine

router = APIRouter()

class RAGQuery(BaseModel):
    query: str
    top_k: int = 5
    source_filter: Optional[str] = None

@router.post("/search")
async def search_knowledge(request: RAGQuery):
    try:
        engine = get_rag_engine()
        results = engine.search(
            query=request.query,
            top_k=request.top_k,
            source_filter=request.source_filter
        )
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_rag_stats():
    try:
        engine = get_rag_engine()
        return engine.stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
