"""Orchestrator agent — routes tasks, manages state, coordinates sub-agents"""
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.agents.base import BaseAgent
from app.agents.guest_agent import GuestAgent
from app.agents.ops_agent import OpsAgent
from app.agents.hsk_agent import HSKAgent
from app.agents.revenue_agent import RevenueAgent
from app.models import AgentLog, Booking
from app.config import settings


class OrchestratorAgent(BaseAgent):
    """Central orchestrator — routes incoming requests to the right agent."""

    def __init__(self):
        super().__init__("orchestrator")
        self.agents = {
            "guest": GuestAgent(),
            "ops": OpsAgent(),
            "hsk": HSKAgent(),
            "revenue": RevenueAgent(),
        }

    async def handle_route(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Route an incoming request to the appropriate sub-agent."""
        request_type = params.get("type", "")
        payload = params.get("payload", {})

        agent_map = {
            "checkin": "guest",
            "checkout": "guest",
            "upsell": "guest",
            "message": "guest",
            "maintenance": "ops",
            "incident": "ops",
            "clean": "hsk",
            "turndown": "hsk",
            "pricing": "revenue",
            "forecast": "revenue",
        }

        target = agent_map.get(request_type, "guest")
        agent = self.agents.get(target)

        if not agent:
            return {
                "status": "error",
                "result": {},
                "confidence": 0.0,
                "message": f"No agent found for request type: {request_type}",
                "decision": "error",
            }

        # Delegate to target agent
        result = await agent.execute(request_type, payload, db)
        return {
            "status": result.get("status", "completed"),
            "result": result.get("result", {}),
            "confidence": result.get("confidence", 1.0),
            "message": result.get("message", ""),
            "decision": result.get("decision", "auto"),
            "routed_to": target,
            "duration_ms": result.get("duration_ms", 0),
        }

    async def handle_status(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Get overall system status summary across all agents."""
        # Count recent agent activity
        log_stmt = select(func.count()).select_from(AgentLog)
        total_logs = (await db.execute(log_stmt)).scalar() or 0

        # Count today's check-ins/outs
        from datetime import date, datetime
        today = date.today()
        checkin_stmt = select(func.count()).select_from(Booking).where(
            Booking.check_in_date == today,
            Booking.status == "confirmed",
        )
        check_ins = (await db.execute(checkin_stmt)).scalar() or 0

        checkout_stmt = select(func.count()).select_from(Booking).where(
            Booking.check_out_date == today,
            Booking.status.in_(["confirmed", "checked_in"]),
        )
        check_outs = (await db.execute(checkout_stmt)).scalar() or 0

        # Agent health
        agent_health = {}
        for name in self.agents:
            enabled = getattr(settings, f"{name.upper()}_AGENT_ENABLED", True)
            agent_health[name] = "active" if enabled else "disabled"

        return {
            "status": "completed",
            "result": {
                "agents": agent_health,
                "total_actions_logged": total_logs,
                "check_ins_today": check_ins,
                "check_outs_today": check_outs,
                "hotel": settings.HOTEL_NAME,
            },
            "confidence": 1.0,
            "message": "All agents operational",
            "decision": "auto",
        }

    async def handle_recent_actions(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Get recent agent actions."""
        limit = params.get("limit", 20)
        stmt = select(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        logs = result.scalars().all()

        return {
            "status": "completed",
            "result": {
                "actions": [
                    {
                        "id": log.id,
                        "agent": log.agent_type,
                        "action": log.action,
                        "decision": log.decision,
                        "confidence": log.confidence,
                        "duration_ms": log.duration_ms,
                        "timestamp": log.created_at.isoformat(),
                    }
                    for log in logs
                ]
            },
            "confidence": 1.0,
            "message": f"Returned {len(logs)} recent actions",
            "decision": "auto",
        }

    async def get_agent(self, agent_type: str):
        """Get a specific sub-agent by type."""
        return self.agents.get(agent_type)
