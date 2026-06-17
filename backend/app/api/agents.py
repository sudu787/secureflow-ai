"""Agents API - Agent activity and analysis."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.agent_action import AgentAction

router = APIRouter()


@router.get("/activity")
async def agent_activity(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent agent activity log."""
    actions = db.query(AgentAction).order_by(AgentAction.created_at.desc()).limit(limit).all()
    return [
        {
            "id": a.id,
            "agent_name": a.agent_name,
            "action_type": a.action_type,
            "input_summary": a.input_summary,
            "output_summary": a.output_summary,
            "confidence": a.confidence,
            "status": a.status,
            "duration_ms": a.duration_ms,
            "related_alert_id": a.related_alert_id,
            "related_ticket_id": a.related_ticket_id,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in actions
    ]


@router.get("/status")
async def agent_status():
    """Get status of all agents including their LLM providers."""
    from app.agents.orchestrator import Orchestrator
    orch = Orchestrator()

    agents = [
        {"name": "triage_agent", "obj": orch.triage},
        {"name": "investigation_agent", "obj": orch.investigation},
        {"name": "remediation_agent", "obj": orch.remediation},
        {"name": "reporting_agent", "obj": orch.reporting},
        {"name": "it_support_agent", "obj": orch.it_support},
    ]

    return {
        "architecture": "multi_agent_multi_llm",
        "total_agents": len(agents),
        "agents": [
            {
                "name": a["obj"].name,
                "description": a["obj"].description,
                "llm_provider": a["obj"].llm_provider,
                "llm_display": "Google Gemini" if a["obj"].llm_provider == "gemini" else ("xAI Grok" if a["obj"].llm_provider == "grok" else "Groq"),
                "capabilities": a["obj"].capabilities,
                "version": a["obj"].version,
                "status": "active",
            }
            for a in agents
        ],
        "llm_providers": {
            "gemini": {"name": "Google Gemini", "model": "gemini-2.0-flash", "agents": ["triage_agent", "remediation_agent"]},
            "grok": {"name": "xAI Grok", "model": "grok-3-mini-fast", "agents": ["investigation_agent", "reporting_agent", "it_support_agent"]},
            "groq": {"name": "Groq", "model": "llama-3.3-70b-versatile", "agents": ["base_agent"]},
        },
    }

