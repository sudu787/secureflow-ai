"""
SecureFlow AI - FastAPI Main Application
Entry point for the backend API server.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db
from app.api import auth, dashboard, alerts, incidents, tickets, chat, demo, agents, events
from app.api import ingestion as ingestion_api
from app.api import notifications as notifications_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("secureflow")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and start background services on startup."""
    # Initialize DB (create tables)
    init_db()

    # Pre-load knowledge base
    try:
        from app.knowledge.knowledge_base import get_knowledge_base
        kb = get_knowledge_base()
        logger.info(f"✅ Knowledge base loaded: {len(kb._documents)} documents")
    except Exception as e:
        logger.warning(f"Knowledge base failed to load: {e}")

    # Start ingestion pipeline if enabled
    ingestion_service = None
    if settings.ENABLE_INGESTION:
        try:
            from app.ingestion.ingestion_service import get_ingestion_service
            ingestion_service = get_ingestion_service()
            ingestion_service.start()
            logger.info("✅ Ingestion pipeline started")
        except Exception as e:
            logger.warning(f"Ingestion service failed to start: {e}")

    yield

    # Shutdown
    if ingestion_service:
        ingestion_service.stop()


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(tickets.router, prefix="/api/tickets", tags=["Tickets"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(demo.router, prefix="/api/demo", tags=["Demo"])
app.include_router(ingestion_api.router, prefix="/api/ingestion", tags=["Ingestion"])
app.include_router(notifications_api.router, prefix="/api/notifications", tags=["Notifications"])


@app.get("/api/health")
async def health_check():
    """Health check with component status."""
    from app.knowledge.knowledge_base import get_knowledge_base
    from app.ingestion.ingestion_service import get_ingestion_service

    kb = get_knowledge_base()
    ingestion = get_ingestion_service()

    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "components": {
            "knowledge_base": {
                "status": "loaded" if kb._loaded else "not_loaded",
                "documents": len(kb._documents),
            },
            "ingestion": {
                "status": "running" if ingestion._running else "stopped",
                "events_ingested": ingestion._stats.get("events_ingested", 0),
            },
            "security": {
                "prompt_injection": "active",
                "output_validation": "active",
                "canary_tokens": "active",
                "policy_engine": "active",
            },
        },
    }
