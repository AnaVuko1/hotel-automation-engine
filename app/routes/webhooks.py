"""Webhook routes — PMS integrations, external system callbacks"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.agents.orchestrator import OrchestratorAgent

router = APIRouter()
orchestrator = OrchestratorAgent()


@router.post("/pms/booking-created")
async def pms_booking_created(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """Handle PMS notification of a new booking."""
    result = await orchestrator.execute("route", {
        "type": "message",
        "payload": {
            "booking_id": payload.get("booking_id"),
            "guest_name": payload.get("guest_name", "Guest"),
            "guest_email": payload.get("guest_email", ""),
            "subject": "Booking Confirmation",
            "body": f"Your booking at Grand Horizon Hotel is confirmed!",
        },
    }, db)
    return {"status": "processed", "result": result}


@router.post("/pms/booking-modified")
async def pms_booking_modified(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """Handle PMS notification of a modified booking."""
    return {"status": "processed", "message": "Booking modification received"}


@router.post("/pms/booking-cancelled")
async def pms_booking_cancelled(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """Handle PMS notification of a cancelled booking."""
    from app.models import Booking
    from sqlalchemy import select

    booking_id = payload.get("booking_id")
    if booking_id:
        stmt = select(Booking).where(Booking.id == booking_id)
        result = await db.execute(stmt)
        booking = result.scalar_one_or_none()
        if booking:
            booking.status = "cancelled"
            await db.commit()

    # Housekeeping: cleanup
    await orchestrator.execute("route", {
        "type": "clean",
        "payload": {"room_number": payload.get("room_number"), "task_type": "touch_up"},
    }, db)

    return {"status": "processed", "message": f"Booking {booking_id} cancelled and cleaned"}


@router.post("/generic")
async def generic_webhook(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """Generic webhook endpoint for external integrations."""
    event_type = payload.get("event_type", "unknown")
    return {
        "status": "received",
        "event_type": event_type,
        "message": "Event queued for processing",
    }
