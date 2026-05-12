"""HSK Agent — housekeeping scheduling, task assignment, turnover coordination"""
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.agents.base import BaseAgent
from app.models import HousekeepingTask, Booking, TaskStatus, TaskPriority


class HSKAgent(BaseAgent):
    """Housekeeping scheduling and coordination agent."""

    def __init__(self):
        super().__init__("hsk")

    async def handle_clean(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Create a cleaning task for a room."""
        task = HousekeepingTask(
            hotel_id=params.get("hotel_id", 1),
            room_number=params.get("room_number", ""),
            task_type=params.get("task_type", "full_clean"),
            priority=params.get("priority", TaskPriority.MEDIUM.value),
            notes=params.get("notes", ""),
            is_checkout_clean=params.get("is_checkout_clean", False),
            is_stayover_clean=params.get("is_stayover_clean", False),
            status=TaskStatus.PENDING.value,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        return {
            "status": "completed",
            "result": {
                "task_id": task.id,
                "room": task.room_number,
                "task_type": task.task_type,
                "status": task.status,
            },
            "confidence": 1.0,
            "message": f"Cleaning task #{task.id} created for room {task.room_number}",
            "decision": "auto",
        }

    async def handle_turndown(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Schedule turndown service for occupied rooms."""
        hotel_id = params.get("hotel_id", 1)
        target_rooms = params.get("rooms", [])

        if not target_rooms:
            # Auto-detect occupied rooms
            today = date.today()
            stmt = select(Booking).where(
                and_(
                    Booking.hotel_id == hotel_id,
                    Booking.check_in_date <= today,
                    Booking.check_out_date > today,
                    Booking.status.in_(["checked_in", "confirmed"]),
                )
            )
            result = await db.execute(stmt)
            bookings = result.scalars().all()
            target_rooms = [b.room_number for b in bookings if b.room_number]

        created = []
        for room in target_rooms:
            task = HousekeepingTask(
                hotel_id=hotel_id,
                room_number=room,
                task_type="turndown",
                priority=TaskPriority.LOW.value,
                status=TaskStatus.PENDING.value,
                notes="Evening turndown service",
                scheduled_time=datetime.now().replace(hour=18, minute=0, second=0),
            )
            db.add(task)
            created.append({"room": room, "task_type": "turndown"})

        await db.commit()

        return {
            "status": "completed",
            "result": {
                "tasks_created": len(created),
                "rooms": [c["room"] for c in created],
            },
            "confidence": 1.0,
            "message": f"Turndown service scheduled for {len(created)} rooms",
            "decision": "auto",
        }

    async def handle_checkout_clean(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Detect and create cleaning tasks for checkout rooms."""
        hotel_id = params.get("hotel_id", 1)
        today = date.today()

        # Find bookings checking out today
        stmt = select(Booking).where(
            and_(
                Booking.hotel_id == hotel_id,
                Booking.check_out_date == today,
                Booking.status.in_(["checked_in", "confirmed"]),
            )
        )
        result = await db.execute(stmt)
        checkouts = result.scalars().all()

        created = []
        for booking in checkouts:
            if booking.room_number:
                task = HousekeepingTask(
                    hotel_id=hotel_id,
                    room_number=booking.room_number,
                    task_type="full_clean",
                    priority=TaskPriority.HIGH.value,
                    status=TaskStatus.PENDING.value,
                    is_checkout_clean=True,
                    notes=f"Checkout clean — {booking.guest_name}",
                )
                db.add(task)
                created.append({"room": booking.room_number, "guest": booking.guest_name})

        await db.commit()

        return {
            "status": "completed",
            "result": {
                "checkouts": len(checkouts),
                "cleaning_tasks": len(created),
                "rooms": [c["room"] for c in created],
            },
            "confidence": 1.0,
            "message": f"Created {len(created)} checkout cleaning tasks for {len(checkouts)} departures",
            "decision": "auto",
        }

    async def handle_daily_batch(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Run the full daily housekeeping batch."""
        hotel_id = params.get("hotel_id", 1)

        # 1. Checkout cleans
        checkout_result = await self.handle_checkout_clean(params, db)
        # 2. Stayover cleans
        stayover_result = await self._schedule_stayover_cleans(hotel_id, db)
        # 3. Turndown
        turndown_result = await self.handle_turndown({"hotel_id": hotel_id}, db)

        return {
            "status": "completed",
            "result": {
                "checkout_cleans": checkout_result.get("result", {}).get("cleaning_tasks", 0),
                "stayover_cleans": stayover_result.get("tasks_created", 0),
                "turndown": turndown_result.get("result", {}).get("tasks_created", 0),
            },
            "confidence": 1.0,
            "message": "Daily housekeeping batch completed",
            "decision": "auto",
        }

    async def _schedule_stayover_cleans(self, hotel_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Schedule stayover cleaning for multi-night guests."""
        from datetime import date, timedelta
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Find guests here 2+ nights (checked in before yesterday)
        stmt = select(Booking).where(
            and_(
                Booking.hotel_id == hotel_id,
                Booking.check_in_date <= yesterday,
                Booking.check_out_date > today,
                Booking.status == "checked_in",
            )
        )
        result = await db.execute(stmt)
        stayovers = result.scalars().all()

        created = 0
        for booking in stayovers:
            if booking.room_number:
                task = HousekeepingTask(
                    hotel_id=hotel_id,
                    room_number=booking.room_number,
                    task_type="touch_up",
                    priority=TaskPriority.MEDIUM.value,
                    status=TaskStatus.PENDING.value,
                    is_stayover_clean=True,
                    notes=f"Stayover clean — {booking.guest_name}",
                )
                db.add(task)
                created += 1
        await db.commit()
        return {"tasks_created": created}

    async def handle_status(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Get housekeeping status summary."""
        hotel_id = params.get("hotel_id", 1)

        counts = {}
        for status in TaskStatus:
            stmt = select(func.count()).select_from(HousekeepingTask).where(
                and_(
                    HousekeepingTask.hotel_id == hotel_id,
                    HousekeepingTask.status == status.value,
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
            "message": f"HSK: {counts.get('pending', 0)} pending, {counts.get('in_progress', 0)} in progress",
            "decision": "auto",
        }
