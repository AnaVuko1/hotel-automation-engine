"""Agent orchestration routes — route requests to agents"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import AgentActionRequest, AgentActionResponse
from app.agents.orchestrator import OrchestratorAgent

router = APIRouter()
orchestrator = OrchestratorAgent()


@router.post("/execute", response_model=AgentActionResponse)
async def execute_agent_action(
    request: AgentActionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Execute an action on a specific agent via the orchestrator."""
    if request.agent == "orchestrator":
        result = await orchestrator.execute(request.action, request.params, db)
    else:
        routed = await orchestrator.handle_route(
            {"type": request.action, "payload": request.params}, db
        )
        result = routed if isinstance(routed, dict) else {"status": "completed", "result": str(routed)}

    return AgentActionResponse(
        agent=request.agent,
        action=request.action,
        status=result.get("status", "error"),
        result=result.get("result", {}),
        confidence=result.get("confidence", 1.0),
        duration_ms=result.get("duration_ms", 0),
        message=result.get("message", ""),
    )


@router.get("/status", response_model=AgentActionResponse)
async def get_agent_status(
    db: AsyncSession = Depends(get_db),
):
    """Get orchestrator status across all agents."""
    result = await orchestrator.execute("status", {}, db)
    return AgentActionResponse(
        agent="orchestrator",
        action="status",
        status=result.get("status", "completed"),
        result=result.get("result", {}),
        confidence=result.get("confidence", 1.0),
        duration_ms=result.get("duration_ms", 0),
        message=result.get("message", ""),
    )


@router.get("/recent", response_model=AgentActionResponse)
async def get_recent_actions(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Get recent agent actions."""
    result = await orchestrator.execute("recent_actions", {"limit": limit}, db)
    return AgentActionResponse(
        agent="orchestrator",
        action="recent_actions",
        status=result.get("status", "completed"),
        result=result.get("result", {}),
        confidence=result.get("confidence", 1.0),
        duration_ms=result.get("duration_ms", 0),
        message=result.get("message", ""),
    )
