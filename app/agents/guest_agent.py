"""Guest Agent — handles check-in/out, upsells, messaging"""
from datetime import date, datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.agents.base import BaseAgent
from app.models import Booking, GuestMessage, RoomType
from app.config import settings


class GuestAgent(BaseAgent):
    """Handles guest-facing operations: check-in, check-out, upsells, messaging."""

    def __init__(self):
        super().__init__("guest")

    async def handle_checkin(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Process an automated check-in."""
        booking_id = params.get("booking_id")
        room_number = params.get("room_number", "")

        if not booking_id:
            return {"status": "error", "result": {}, "message": "booking_id required", "confidence": 0.0, "decision": "error"}

        stmt = select(Booking).where(Booking.id == booking_id)
        result = await db.execute(stmt)
        booking = result.scalar_one_or_none()

        if not booking:
            return {"status": "error", "result": {}, "message": f"Booking {booking_id} not found", "confidence": 0.0, "decision": "error"}

        booking.status = "checked_in"
        if room_number:
            booking.room_number = room_number

        # Send welcome message
        welcome_msg = GuestMessage(
            hotel_id=booking.hotel_id,
            booking_id=booking.id,
            guest_name=booking.guest_name,
            guest_email=booking.guest_email,
            channel="email",
            direction="outbound",
            subject=f"Welcome to {settings.HOTEL_NAME}!",
            body=f"Dear {booking.guest_name},\n\nWelcome to {settings.HOTEL_NAME}! "
                 f"Your room {room_number or 'will be assigned shortly'} is ready.\n"
                 f"Check-in: {booking.check_in_date}\n"
                 f"Check-out: {booking.check_out_date}\n\n"
                 f"We hope you enjoy your stay.\n\nBest regards,\n{settings.HOTEL_NAME} Team",
            agent_type="guest",
            auto_generated=True,
        )
        db.add(welcome_msg)
        await db.commit()

        return {
            "status": "completed",
            "result": {
                "booking_id": booking.id,
                "guest": booking.guest_name,
                "room_number": room_number,
                "status": "checked_in",
                "welcome_sent": True,
            },
            "confidence": 1.0,
            "message": f"Check-in completed for {booking.guest_name}",
            "decision": "auto",
        }

    async def handle_checkout(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Process an automated check-out."""
        booking_id = params.get("booking_id")

        if not booking_id:
            return {"status": "error", "result": {}, "message": "booking_id required", "confidence": 0.0, "decision": "error"}

        stmt = select(Booking).where(Booking.id == booking_id)
        result = await db.execute(stmt)
        booking = result.scalar_one_or_none()

        if not booking:
            return {"status": "error", "result": {}, "message": f"Booking {booking_id} not found", "confidence": 0.0, "decision": "error"}

        booking.status = "checked_out"

        # Send thank you / feedback request
        feedback_msg = GuestMessage(
            hotel_id=booking.hotel_id,
            booking_id=booking.id,
            guest_name=booking.guest_name,
            guest_email=booking.guest_email,
            channel="email",
            direction="outbound",
            subject=f"Thank you for staying at {settings.HOTEL_NAME}!",
            body=f"Dear {booking.guest_name},\n\nThank you for choosing {settings.HOTEL_NAME}. "
                 f"We hope you had a wonderful stay.\n\n"
                 f"Please take a moment to share your feedback:\n"
                 f"https://grandhorizonhotel.com/feedback/{booking.id}\n\n"
                 f"Book your next stay directly and save 15%:\n"
                 f"https://grandhorizonhotel.com/rebook\n\n"
                 f"Best regards,\n{settings.HOTEL_NAME} Team",
            agent_type="guest",
            auto_generated=True,
        )
        db.add(feedback_msg)
        await db.commit()

        return {
            "status": "completed",
            "result": {
                "booking_id": booking.id,
                "guest": booking.guest_name,
                "status": "checked_out",
                "feedback_sent": True,
            },
            "confidence": 1.0,
            "message": f"Check-out completed for {booking.guest_name}",
            "decision": "auto",
        }

    async def handle_upsell(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Generate and send an upsell offer to a guest."""
        booking_id = params.get("booking_id")
        offer_type = params.get("offer_type", "room_upgrade")
        offer_details = params.get("offer_details", {})

        if not booking_id:
            return {"status": "error", "result": {}, "message": "booking_id required", "confidence": 0.0, "decision": "error"}

        stmt = select(Booking).where(Booking.id == booking_id)
        result = await db.execute(stmt)
        booking = result.scalar_one_or_none()

        if not booking:
            return {"status": "error", "result": {}, "message": f"Booking {booking_id} not found", "confidence": 0.0, "decision": "error"}

        offers = {
            "room_upgrade": {
                "subject": f"Upgrade Your Stay at {settings.HOTEL_NAME}",
                "body": f"Dear {booking.guest_name},\n\nWe have a special upgrade available for your upcoming stay. "
                        f"Elevate your experience with a premium room for just ${offer_details.get('upgrade_price', 50)}/night.\n\n"
                        f"Reply to this email to confirm your upgrade.\n\nBest regards,\n{settings.HOTEL_NAME} Team",
            },
            "late_checkout": {
                "subject": f"Extend Your Stay — Late Checkout Offer",
                "body": f"Dear {booking.guest_name},\n\nNeed more time? We're offering a late checkout until "
                        f"{offer_details.get('late_time', '4:00 PM')} for just ${offer_details.get('price', 30)}.\n\n"
                        f"Reply to confirm.\n\nBest regards,\n{settings.HOTEL_NAME} Team",
            },
            "spa": {
                "subject": f"Spa & Wellness — Special Guest Offer",
                "body": f"Dear {booking.guest_name},\n\nTreat yourself to our world-class spa during your stay. "
                        f"We're offering {offer_details.get('discount', '20%')} off all treatments when booked in advance.\n\n"
                        f"View packages: https://grandhorizonhotel.com/spa\n\nBest regards,\n{settings.HOTEL_NAME} Team",
            },
            "dining": {
                "subject": f"Exclusive Dining Experience at {settings.HOTEL_NAME}",
                "body": f"Dear {booking.guest_name},\n\nReserve a table at our signature restaurant and enjoy "
                        f"{offer_details.get('offer', 'a complimentary welcome drink')}.\n\n"
                        f"Book now: https://grandhorizonhotel.com/dining\n\nBest regards,\n{settings.HOTEL_NAME} Team",
            },
        }

        offer = offers.get(offer_type, offers["room_upgrade"])

        msg = GuestMessage(
            hotel_id=booking.hotel_id,
            booking_id=booking.id,
            guest_name=booking.guest_name,
            guest_email=booking.guest_email,
            channel="email",
            direction="outbound",
            subject=offer["subject"],
            body=offer["body"],
            agent_type="guest",
            auto_generated=True,
        )
        db.add(msg)
        await db.commit()

        return {
            "status": "completed",
            "result": {
                "booking_id": booking.id,
                "guest": booking.guest_name,
                "offer_type": offer_type,
                "offer_sent": True,
                "offer_value": offer_details.get("price", 0),
            },
            "confidence": 1.0,
            "message": f"Upsell offer '{offer_type}' sent to {booking.guest_name}",
            "decision": "auto",
        }

    async def handle_message(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Send an automated message to a guest."""
        booking_id = params.get("booking_id")
        guest_name = params.get("guest_name", "Guest")
        guest_email = params.get("guest_email")
        subject = params.get("subject", "")
        body = params.get("body", "")

        msg = GuestMessage(
            hotel_id=params.get("hotel_id", 1),
            booking_id=booking_id,
            guest_name=guest_name,
            guest_email=guest_email,
            channel=params.get("channel", "email"),
            direction="outbound",
            subject=subject,
            body=body,
            agent_type="guest",
            auto_generated=True,
        )
        db.add(msg)
        await db.commit()

        return {
            "status": "completed",
            "result": {"message_id": msg.id, "sent_to": guest_name},
            "confidence": 1.0,
            "message": f"Message sent to {guest_name}",
            "decision": "auto",
        }

    async def handle_late_checkout(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Handle a late checkout request."""
        booking_id = params.get("booking_id")
        requested_time = params.get("requested_time", "14:00")

        stmt = select(Booking).where(Booking.id == booking_id)
        result = await db.execute(stmt)
        booking = result.scalar_one_or_none()

        if not booking:
            return {"status": "error", "result": {}, "message": "Booking not found", "confidence": 0.0, "decision": "error"}

        # Auto-approve late checkout up to 2PM, escalate after
        if requested_time <= "14:00":
            return {
                "status": "completed",
                "result": {"approved": True, "new_checkout_time": requested_time},
                "confidence": 1.0,
                "message": f"Late checkout until {requested_time} approved",
                "decision": "auto",
            }

        return {
            "status": "completed",
            "result": {"approved": False, "reason": "Requires manager approval"},
            "confidence": 0.5,
            "message": f"Late checkout until {requested_time} requires manager approval",
            "decision": "escalated",
        }
