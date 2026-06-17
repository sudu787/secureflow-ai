"""Demo API - Demo scenario control panel."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.demo.simulator import SCENARIOS, run_scenario, run_all_scenarios

router = APIRouter()


@router.get("/scenarios")
async def list_scenarios():
    """List all available demo scenarios."""
    return [
        {
            "id": sid,
            "name": s["name"],
            "description": s["description"],
            "type": s["type"],
        }
        for sid, s in SCENARIOS.items()
    ]


@router.post("/start/{scenario_id}")
async def start_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """Run a specific demo scenario."""
    if scenario_id not in SCENARIOS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Unknown scenario: {scenario_id}")

    result = run_scenario(scenario_id, db)
    return result


@router.post("/start-all")
async def start_all_scenarios(db: Session = Depends(get_db)):
    """Run all demo scenarios."""
    results = run_all_scenarios(db)
    return {"scenarios_run": len(results), "results": results}


@router.post("/reset")
async def reset_demo(db: Session = Depends(get_db)):
    """Reset all demo data."""
    from app.models import Event, Alert, Incident, Ticket, AgentAction, AuditLog, ChatSession
    for model in [AgentAction, AuditLog, ChatSession, Ticket, Incident, Alert, Event]:
        db.query(model).delete()
    db.commit()
    return {"status": "reset", "message": "All demo data has been cleared."}
