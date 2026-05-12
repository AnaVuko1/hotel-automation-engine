"""Hotel Automation Engine — Multi-agent AI system for end-to-end hotel operations"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.HOTEL_NAME} Automation Engine")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Hotel Automation Engine",
    description="Multi-agent AI system for end-to-end hotel operations automation",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Mount Routes ────────────────────────────────────────────────────────────

from app.routes import agents, operations, analytics, webhooks
from app.adapters import schema_org

app.include_router(agents.router, prefix="/api/v1/agents", tags=["AI Agents"])
app.include_router(operations.router, prefix="/api/v1/operations", tags=["Operations"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])


# ─── Schema.org AI Discovery Endpoints ───────────────────────────────────────

@app.get("/api/v1/agent-inventory/hotel", tags=["AI Agent Inventory"])
async def get_hotel_inventory():
    """Get complete hotel schema.org JSON-LD for AI agent discovery."""
    return schema_org.generate_hotel_jsonld()


@app.get("/api/v1/agent-inventory/rooms", tags=["AI Agent Inventory"])
async def get_rooms_inventory():
    """Get all room types with schema.org JSON-LD formatting."""
    return schema_org.generate_rooms_jsonld()


@app.get("/api/v1/agent-inventory/availability", tags=["AI Agent Inventory"])
async def get_availability(request: Request):
    """Get real-time availability with schema.org JSON-LD formatting."""
    from datetime import date, timedelta
    from app.database import AsyncSessionLocal
    from app.adapters.schema_org import generate_availability_jsonld

    checkin = request.query_params.get("checkin", date.today().isoformat())
    checkout = request.query_params.get("checkout", (date.today() + timedelta(days=3)).isoformat())

    async with AsyncSessionLocal() as db:
        return await generate_availability_jsonld(
            date.fromisoformat(checkin),
            date.fromisoformat(checkout),
            db,
        )


@app.get("/.well-known/ai-agent.json", tags=["Discovery"])
async def ai_agent_discovery():
    """AI agent discovery endpoint — like robots.txt for AI agents."""
    return {
        "name": f"{settings.HOTEL_NAME} - Automation Engine",
        "description": "Multi-agent AI system for hotel operations automation",
        "version": "1.0.0",
        "capabilities": [
            "hotel_operations_automation",
            "guest_checkin_checkout",
            "maintenance_ticketing",
            "housekeeping_scheduling",
            "dynamic_pricing",
            "upsell_generation",
            "messaging_automation",
        ],
        "agents": ["orchestrator", "guest", "ops", "hsk", "revenue"],
        "endpoints": {
            "agent_execute": "/api/v1/agents/execute",
            "hotel_inventory": "/api/v1/agent-inventory/hotel",
            "rooms": "/api/v1/agent-inventory/rooms",
            "availability": "/api/v1/agent-inventory/availability",
            "analytics": "/api/v1/analytics/metrics",
            "docs": "/docs",
        },
    }


# ─── Root ───────────────────────────────────────────────────────────────────

@app.get("/", tags=["System"])
async def root():
    """Root endpoint — API is alive."""
    return {
        "service": "Hotel Automation Engine",
        "version": "1.0.0",
        "hotel": settings.HOTEL_NAME,
        "docs": "/docs",
        "health": "/health",
        "agents": {
            "orchestrator": "Central task router",
            "guest": "Check-in/out, upsells, messaging",
            "ops": "Maintenance, incidents, staff routing",
            "hsk": "Housekeeping scheduling, turndown",
            "revenue": "Dynamic pricing, forecasting, reports",
        },
    }


@app.get("/health", tags=["System"])
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "hotel-automation-engine", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
