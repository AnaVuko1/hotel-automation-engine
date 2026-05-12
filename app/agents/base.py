"""Base agent class for all hotel automation agents"""
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AgentLog
import time


class BaseAgent:
    """Base class with shared logging, timing, and escalation logic."""

    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.name = f"{agent_type}_agent"

    async def _log(
        self,
        action: str,
        db: AsyncSession,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        input_data: Optional[dict] = None,
        output_data: Optional[dict] = None,
        decision: str = "auto",
        confidence: float = 1.0,
        duration_ms: int = 0,
    ) -> None:
        """Persist an agent action log."""
        log = AgentLog(
            agent_type=self.agent_type,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            input_data=input_data or {},
            output_data=output_data or {},
            decision=decision,
            confidence=confidence,
            duration_ms=duration_ms,
        )
        db.add(log)
        await db.commit()

    async def execute(
        self, action: str, params: Dict[str, Any], db: AsyncSession
    ) -> Dict[str, Any]:
        """Execute an agent action with timing and logging."""
        start = time.time()
        try:
            handler = getattr(self, f"handle_{action}", None)
            if not handler:
                return {
                    "status": "error",
                    "result": {},
                    "message": f"Action '{action}' not implemented for {self.agent_type} agent",
                }
            result = await handler(params, db)
            duration = int((time.time() - start) * 1000)
            await self._log(
                action=action,
                db=db,
                input_data=params,
                output_data=result.get("result", result) if isinstance(result, dict) else {"output": str(result)},
                decision=result.get("decision", "auto") if isinstance(result, dict) else "auto",
                confidence=result.get("confidence", 1.0) if isinstance(result, dict) else 1.0,
                duration_ms=duration,
            )
            if isinstance(result, dict):
                result["duration_ms"] = duration
                return result
            return {
                "status": "completed",
                "result": result,
                "confidence": 1.0,
                "duration_ms": duration,
                "message": "",
                "decision": "auto",
            }
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            await self._log(
                action=action,
                db=db,
                input_data=params,
                output_data={"error": str(e)},
                decision="error",
                confidence=0.0,
                duration_ms=duration,
            )
            return {
                "status": "error",
                "result": {},
                "confidence": 0.0,
                "duration_ms": duration,
                "message": str(e),
            }

    def should_escalate(self, confidence: float, threshold: float = 0.6) -> bool:
        """Determine if an action requires human escalation."""
        return confidence < threshold
