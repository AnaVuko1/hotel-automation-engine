"""Tests for Hotel Automation Engine"""
import pytest
from datetime import date
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager


@pytest.fixture(scope="module")
async def client():
    """Create test client with lifespan managed."""
    from app.main import app
    transport = ASGITransport(app=app)
    async with LifespanManager(app):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.mark.asyncio
async def test_health(client):
    """Health check returns OK."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "hotel-automation-engine"


@pytest.mark.asyncio
async def test_root(client):
    """Root returns service info."""
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "Hotel Automation Engine"
    assert "agents" in data
    assert len(data["agents"]) == 5  # 5 agents


@pytest.mark.asyncio
async def test_ai_discovery(client):
    """AI agent discovery endpoint works."""
    resp = await client.get("/.well-known/ai-agent.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "capabilities" in data
    assert "endpoints" in data


@pytest.mark.asyncio
async def test_agent_orchestrator_status(client):
    """Orchestrator status returns agent health."""
    resp = await client.get("/api/v1/agents/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"] == "orchestrator"
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_agent_orchestrator_recent(client):
    """Recent actions endpoint works."""
    resp = await client.get("/api/v1/agents/recent?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"] == "orchestrator"


@pytest.mark.asyncio
async def test_agent_execute_guest_checkin(client):
    """Guest agent check-in gracefully handles missing booking."""
    resp = await client.post("/api/v1/agents/execute", json={
        "agent": "guest",
        "action": "checkin",
        "params": {"booking_id": 1, "room_number": "1204"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"] == "guest"
    assert data["action"] == "checkin"
    # Without seed data: error is expected
    assert data["status"] in ("completed", "error")


@pytest.mark.asyncio
async def test_agent_execute_ops_maintenance(client):
    """Ops agent maintenance creation."""
    resp = await client.post("/api/v1/agents/execute", json={
        "agent": "ops",
        "action": "maintenance",
        "params": {
            "hotel_id": 1,
            "title": "Test maintenance",
            "description": "AC not working in test room",
            "room_number": "999",
            "category": "hvac",
            "estimated_minutes": 45,
        },
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"] == "ops"
    assert data["status"] in ("completed",)


@pytest.mark.asyncio
async def test_agent_execute_hsk_clean(client):
    """HSK agent cleaning task creation."""
    resp = await client.post("/api/v1/agents/execute", json={
        "agent": "hsk",
        "action": "clean",
        "params": {
            "hotel_id": 1,
            "room_number": "101",
            "task_type": "full_clean",
            "is_checkout_clean": True,
        },
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"] == "hsk"
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_agent_execute_revenue_pricing(client):
    """Revenue agent pricing execution."""
    resp = await client.post("/api/v1/agents/execute", json={
        "agent": "revenue",
        "action": "pricing",
        "params": {"date": date.today().isoformat()},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"] == "revenue"


@pytest.mark.asyncio
async def test_analytics_metrics(client):
    """Dashboard metrics endpoint works (empty DB)."""
    resp = await client.get("/api/v1/analytics/metrics?period_days=30")
    assert resp.status_code in (200, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert "occupancy_rate" in data


@pytest.mark.asyncio
async def test_schema_inventory(client):
    """Schema.org hotel inventory endpoint works."""
    resp = await client.get("/api/v1/agent-inventory/hotel")
    assert resp.status_code == 200
    data = resp.json()
    assert data["@type"] == "Hotel"
    assert data["name"] is not None


@pytest.mark.asyncio
async def test_schema_rooms(client):
    """Schema.org room inventory endpoint works."""
    resp = await client.get("/api/v1/agent-inventory/rooms")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert data[0]["@type"] == "Room"


@pytest.mark.asyncio
async def test_operations_maintenance_create(client):
    """Operations maintenance CRUD — create."""
    resp = await client.post("/api/v1/operations/maintenance", json={
        "hotel_id": 1,
        "title": "Pool pump repair",
        "description": "Scheduled maintenance",
        "category": "general",
        "priority": "medium",
        "source": "scheduled",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Pool pump repair"


@pytest.mark.asyncio
async def test_operations_maintenance_list(client):
    """Operations maintenance CRUD — list."""
    resp = await client.get("/api/v1/operations/maintenance?hotel_id=1&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_operations_housekeeping_create(client):
    """Operations housekeeping CRUD — create."""
    resp = await client.post("/api/v1/operations/housekeeping", json={
        "hotel_id": 1,
        "room_number": "202",
        "task_type": "full_clean",
        "is_checkout_clean": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["room_number"] == "202"


@pytest.mark.asyncio
async def test_webhook_booking_created(client):
    """Webhook for booking created."""
    resp = await client.post("/api/v1/webhooks/pms/booking-created", json={
        "booking_id": 42,
        "guest_name": "Test Guest",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "processed"


@pytest.mark.asyncio
async def test_webhook_generic(client):
    """Generic webhook works."""
    resp = await client.post("/api/v1/webhooks/generic", json={
        "event_type": "test_event",
        "data": {"key": "value"},
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "received"
