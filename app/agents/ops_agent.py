"""Ops Agent — handles maintenance requests, incident triage, staff routing"""
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.agents.base import BaseAgent
from app.models import MaintenanceTask, TaskStatus, TaskPriority


class OpsAgent(BaseAgent):
    """Maintenance and operations coordination agent."""

    def __init__(self):
        super().__init__("ops")

    async def handle_maintenance(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Create and triage a maintenance request."""
        task = MaintenanceTask(
            hotel_id=params.get("hotel_id", 1),
            title=params.get("title", "Maintenance Request"),
            description=params.get("description", ""),
            room_number=params.get("room_number"),
            category=params.get("category", "general"),
            priority=self._triage_priority(params),
            status=TaskStatus.PENDING.value,
            reported_by=params.get("reported_by", "guest"),
            source=params.get("source", "guest_request"),
            estimated_minutes=params.get("estimated_minutes", 30),
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        # Auto-assign by category if staff available
        assigned = False
        assigned_to = None
        if task.priority in ("high", "urgent"):
            assigned_to = self._recommend_staff(task.category)
            if assigned_to:
                task.assigned_to = assigned_to
                task.status = TaskStatus.ASSIGNED.value
                assigned = True
                await db.commit()

        return {
            "status": "completed",
            "result": {
                "task_id": task.id,
                "title": task.title,
                "priority": task.priority,
                "category": task.category,
                "assigned": assigned,
                "assigned_to": assigned_to,
                "status": task.status,
            },
            "confidence": 0.9 if assigned else 0.7,
            "message": f"Maintenance task #{task.id} created. Priority: {task.priority}." +
                       (f" Assigned to {assigned_to}." if assigned else " Pending assignment."),
            "decision": "auto" if assigned else "scheduled",
        }

    async def handle_incident(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Handle an urgent incident — always escalate to human."""
        task = MaintenanceTask(
            hotel_id=params.get("hotel_id", 1),
            title=f"INCIDENT: {params.get('title', 'Urgent Issue')}",
            description=params.get("description", ""),
            room_number=params.get("room_number"),
            category="incident",
            priority=TaskPriority.URGENT.value,
            status=TaskStatus.ASSIGNED.value,
            reported_by=params.get("reported_by", "guest"),
            source="incident",
            estimated_minutes=params.get("estimated_minutes", 15),
            assigned_to="Manager-on-Duty",
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        return {
            "status": "completed",
            "result": {
                "task_id": task.id,
                "title": task.title,
                "priority": "urgent",
                "escalated_to": "Manager-on-Duty",
            },
            "confidence": 1.0,
            "message": f"INCIDENT #{task.id} created and escalated to Manager-on-Duty",
            "decision": "escalated",
        }

    async def handle_status(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Get maintenance operations status summary."""
        hotel_id = params.get("hotel_id", 1)

        counts = {}
        for status in TaskStatus:
            stmt = select(func.count()).select_from(MaintenanceTask).where(
                and_(
                    MaintenanceTask.hotel_id == hotel_id,
                    MaintenanceTask.status == status.value,
                )
            )
            result = await db.execute(stmt)
            counts[status.value] = result.scalar() or 0

        return {
            "status": "completed",
            "result": {
                "total": sum(counts.values()),
                "by_status": counts,
            },
            "confidence": 1.0,
            "message": f"Maintenance: {counts.get('pending', 0)} pending, {counts.get('in_progress', 0)} in progress",
            "decision": "auto",
        }

    def _triage_priority(self, params: Dict[str, Any]) -> str:
        """Determine priority based on category and description."""
        category = params.get("category", "general").lower()
        desc = params.get("description", "").lower()
        title = params.get("title", "").lower()

        urgent_keywords = ["leak", "flood", "fire", "gas", "no power", "lock", "broken",
                           "emergency", "water", "electrical", "smoke", "ac not working",
                           "heating not working", "no hot water"]

        if category == "incident":
            return TaskPriority.URGENT.value
        if any(kw in desc or kw in title for kw in urgent_keywords):
            return TaskPriority.HIGH.value
        if category in ("plumbing", "electrical", "hvac"):
            return TaskPriority.HIGH.value
        return TaskPriority.MEDIUM.value

    def _recommend_staff(self, category: str) -> str:
        """Recommend a staff member based on task category."""
        staff_map = {
            "plumbing": "Plumber-on-Duty",
            "electrical": "Electrician-on-Duty",
            "hvac": "HVAC-Technician",
            "general": "Maintenance-Team",
            "incident": "Manager-on-Duty",
        }
        return staff_map.get(category, "Maintenance-Team")
