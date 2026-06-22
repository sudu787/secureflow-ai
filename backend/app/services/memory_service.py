"""
SecureFlow AI - Memory Service
Handles memory consolidation and retrieval logic.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.memory import IncidentMemory, SessionMemory
from app.models.alert import Alert
from app.knowledge.rag_engine import get_rag_engine
import logging
import time

logger = logging.getLogger(__name__)

class MemoryService:
    @staticmethod
    def consolidate_alert_to_memory(db: Session, alert_id: int) -> Optional[IncidentMemory]:
        """Simulates nightly consolidation: takes a resolved alert, extracts lessons, stores in DB & Vector DB."""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None
            
        # Simulated LLM Summary (In production, an agent would write this)
        summary = f"Alert '{alert.title}' involved tactics {alert.mitre_tactic or 'Unknown'}. Automatically triaged and investigated."
        mitigation = alert.remediation_plan or "Standard containment procedures were followed. Host isolated."
        iocs = alert.evidence if alert.evidence else {"ips": [alert.source_ip] if alert.source_ip else []}
        
        # Save to SQLite
        memory = IncidentMemory(
            original_alert_id=alert.id,
            title=f"Incident Memory: {alert.title}",
            root_cause_summary=summary,
            mitigation_applied=mitigation,
            iocs=iocs,
            vector_id=f"mem_alert_{alert.id}_{int(time.time())}"
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        
        # Save to ChromaDB via RAG Engine
        try:
            rag = get_rag_engine()
            doc_text = f"Title: {memory.title}\nRoot Cause: {memory.root_cause_summary}\nMitigation: {memory.mitigation_applied}"
            rag.add_incident_memory(
                memory_id=memory.vector_id,
                text=doc_text,
                metadata={
                    "source": "incident_memory",
                    "original_alert_id": alert.id,
                    "title": memory.title
                }
            )
            logger.info(f"Successfully embedded memory {memory.vector_id} into ChromaDB.")
        except Exception as e:
            logger.error(f"Failed to embed memory into ChromaDB: {e}")
            
        return memory

    @staticmethod
    def get_recent_memories(db: Session, limit: int = 10) -> List[IncidentMemory]:
        return db.query(IncidentMemory).order_by(IncidentMemory.created_at.desc()).limit(limit).all()
