"""Ingestion API — Monitor and control the log ingestion pipeline."""

from fastapi import APIRouter
from app.ingestion.ingestion_service import get_ingestion_service

router = APIRouter()


@router.get("/status")
async def ingestion_status():
    """Get the current ingestion pipeline status."""
    service = get_ingestion_service()
    return service.status


@router.post("/start")
async def start_ingestion():
    """Start the log ingestion pipeline."""
    service = get_ingestion_service()
    service.start()
    return {"status": "started", "message": "Log ingestion pipeline started"}


@router.post("/stop")
async def stop_ingestion():
    """Stop the log ingestion pipeline."""
    service = get_ingestion_service()
    service.stop()
    return {"status": "stopped", "message": "Log ingestion pipeline stopped"}
