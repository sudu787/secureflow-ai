"""Tickets API - IT support and incident ticket management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.ticket import Ticket
from app.schemas.tickets import TicketCreate, TicketResponse, TicketUpdate

router = APIRouter()


@router.get("", response_model=list[TicketResponse])
async def list_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    if category:
        query = query.filter(Ticket.category == category)
    if priority:
        query = query.filter(Ticket.priority == priority)
    return query.order_by(Ticket.created_at.desc()).offset(offset).limit(limit).all()


@router.post("", response_model=TicketResponse)
async def create_ticket(data: TicketCreate, db: Session = Depends(get_db)):
    ticket = Ticket(
        title=data.title,
        description=data.description,
        category=data.category,
        priority=data.priority,
        requester=data.requester,
        owner=data.owner,
        source=data.source,
        related_incident_id=data.related_incident_id,
        related_alert_id=data.related_alert_id,
        tags=data.tags,
        timeline=[{
            "timestamp": datetime.utcnow().isoformat(),
            "action": "Ticket created",
            "actor": data.requester or "system",
        }],
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(ticket_id: int, data: TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ticket, key, value)

    # Add to timeline
    timeline = ticket.timeline or []
    timeline.append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": f"Ticket updated: {', '.join(update_data.keys())}",
        "actor": "system",
    })
    ticket.timeline = timeline

    if data.status == "resolved":
        ticket.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)
    return ticket
