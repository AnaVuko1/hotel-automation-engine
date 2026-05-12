"""Autonomous pricing engine that calculates optimal room prices"""
from datetime import date, timedelta
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.config import settings
from app.models import RoomType, Booking, PricingHistory, LocalEvent


class PricingEngine:
    """Revenue-aware dynamic pricing engine."""

    def __init__(self):
        self.base_prices = {
            "standard": settings.BASE_PRICE_STANDARD,
            "deluxe": settings.BASE_PRICE_DELUXE,
            "suite": settings.BASE_PRICE_SUITE,
        }

    async def calculate_price(self, room_type_id: int, target_date: date, db: AsyncSession) -> float:
        """Calculate final price for a room type on a specific date."""
        stmt = select(RoomType).where(RoomType.id == room_type_id)
        result = await db.execute(stmt)
        room_type = result.scalar_one_or_none()
        if not room_type:
            raise ValueError(f"Room type {room_type_id} not found")

        base_price = room_type.base_price
        occupancy_mult = await self._occupancy_multiplier(room_type_id, target_date, db)
        season_mult = self._season_multiplier(target_date)
        urgency_mult = self._urgency_multiplier(target_date)
        event_mult = await self._event_multiplier(target_date, db)

        final_price = base_price * occupancy_mult * season_mult * urgency_mult * event_mult

        # Clamp within reasonable bounds
        min_price = base_price * 0.5
        max_price = base_price * 2.0
        final_price = max(min_price, min(max_price, final_price))

        return round(final_price, 2)

    async def _occupancy_multiplier(self, room_type_id: int, target_date: date, db: AsyncSession) -> float:
        """Higher occupancy → higher price."""
        stmt = select(func.count()).select_from(Booking).where(
            and_(
                Booking.room_type_id == room_type_id,
                Booking.check_in_date <= target_date,
                Booking.check_out_date > target_date,
                Booking.status.in_(["confirmed", "checked_in"]),
            )
        )
        result = await db.execute(stmt)
        booked = result.scalar() or 0

        total_stmt = select(RoomType.total_count).where(RoomType.id == room_type_id)
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 1

        occupancy_rate = booked / total
        return settings.OCCUPANCY_MULT_MIN + (settings.OCCUPANCY_MULT_MAX - settings.OCCUPANCY_MULT_MIN) * occupancy_rate

    def _season_multiplier(self, target_date: date) -> float:
        """Seasonal multiplier based on month."""
        month = target_date.month
        # Peak: Dec-Feb, Jun-Aug
        if month in [12, 1, 2, 6, 7, 8]:
            return 1.2
        # Shoulder: Mar-May, Sep-Oct
        elif month in [3, 4, 5, 9, 10]:
            return 1.0
        # Off-peak: November
        else:
            return 0.85

    def _urgency_multiplier(self, target_date: date) -> float:
        """Urgency multiplier based on how close the date is."""
        days_until = (target_date - date.today()).days
        if days_until < 0:
            return 0.9  # last minute
        elif days_until <= 3:
            return 1.3  # high urgency
        elif days_until <= 7:
            return 1.15
        elif days_until <= 30:
            return 1.0
        else:
            return 0.95  # far out — discount for early booking

    async def _event_multiplier(self, target_date: date, db: AsyncSession) -> float:
        """Event multiplier — local events drive prices up."""
        stmt = select(LocalEvent).where(
            and_(
                LocalEvent.event_date == target_date,
            )
        )
        result = await db.execute(stmt)
        events = result.scalars().all()
        if not events:
            return 1.0
        return max(e.impact_multiplier for e in events)

    async def get_current_pricing(self, target_date: date, db: AsyncSession) -> List[dict]:
        """Get current pricing for all room types."""
        stmt = select(RoomType)
        result = await db.execute(stmt)
        room_types = result.scalars().all()

        pricing = []
        for rt in room_types:
            final_price = await self.calculate_price(rt.id, target_date, db)
            pricing.append({
                "room_type_id": rt.id,
                "room_type": rt.name,
                "base_price": rt.base_price,
                "final_price": final_price,
                "currency": "USD",
                "date": target_date.isoformat(),
            })
        return pricing

    async def get_pricing_history(
        self, room_type_id: int, start_date: date, end_date: date, db: AsyncSession
    ) -> List[dict]:
        """Get pricing history for a specific room type."""
        stmt = select(PricingHistory).where(
            and_(
                PricingHistory.room_type_id == room_type_id,
                PricingHistory.date >= start_date,
                PricingHistory.date <= end_date,
            )
        ).order_by(PricingHistory.date)
        result = await db.execute(stmt)
        return [
            {
                "date": ph.date.isoformat(),
                "base_price": ph.base_price,
                "final_price": ph.final_price,
                "occupancy_mult": ph.occupancy_mult,
                "season_mult": ph.season_mult,
                "urgency_mult": ph.urgency_mult,
                "event_mult": ph.event_mult,
                "occupancy_rate": ph.occupancy_rate,
            }
            for ph in result.scalars().all()
        ]

    async def recalculate_pricing(self, target_date: date, db: AsyncSession) -> dict:
        """Recalculate and persist pricing for a specific date."""
        stmt = select(RoomType)
        result = await db.execute(stmt)
        room_types = result.scalars().all()

        updated = []
        for rt in room_types:
            final_price = await self.calculate_price(rt.id, target_date, db)
            updated.append({
                "room_type_id": rt.id,
                "room_type": rt.name,
                "final_price": final_price,
            })
        return {"date": target_date.isoformat(), "pricing": updated}

    async def calculate_occupancy_rate(self, start_date: date, end_date: date, db: AsyncSession) -> float:
        """Calculate average occupancy rate over a date range."""
        stmt = select(func.avg(PricingHistory.occupancy_rate)).where(
            and_(
                PricingHistory.date >= start_date,
                PricingHistory.date <= end_date,
            )
        )
        result = await db.execute(stmt)
        rate = result.scalar()
        return round(rate, 4) if rate else 0.0

    async def calculate_average_daily_rate(self, start_date: date, end_date: date, db: AsyncSession) -> float:
        """Calculate average daily rate (ADR)."""
        stmt = select(func.avg(PricingHistory.final_price)).where(
            and_(
                PricingHistory.date >= start_date,
                PricingHistory.date <= end_date,
            )
        )
        result = await db.execute(stmt)
        adr = result.scalar()
        return round(adr, 2) if adr else 0.0

    async def calculate_revpar(self, start_date: date, end_date: date, db: AsyncSession) -> float:
        """Calculate Revenue Per Available Room."""
        adr = await self.calculate_average_daily_rate(start_date, end_date, db)
        occ = await self.calculate_occupancy_rate(start_date, end_date, db)
        return round(adr * occ, 2)

    async def calculate_total_revenue(self, start_date: date, end_date: date, db: AsyncSession) -> float:
        """Calculate total revenue from bookings."""
        stmt = select(func.sum(Booking.total_price)).where(
            and_(
                Booking.check_in_date >= start_date,
                Booking.check_in_date <= end_date,
                Booking.status.in_(["confirmed", "checked_in", "checked_out"]),
            )
        )
        result = await db.execute(stmt)
        rev = result.scalar()
        return round(rev, 2) if rev else 0.0

    async def get_revenue_trend(self, months: int, db: AsyncSession) -> List[dict]:
        """Get monthly revenue trend."""
        from sqlalchemy import extract
        stmt = select(
            extract("year", Booking.check_in_date).label("year"),
            extract("month", Booking.check_in_date).label("month"),
            func.sum(Booking.total_price).label("revenue"),
            func.sum(func.case(
                (Booking.is_direct_booking == True, Booking.total_price), else_=0
            )).label("direct_revenue"),
        ).where(
            Booking.status.in_(["confirmed", "checked_in", "checked_out"]),
        ).group_by("year", "month").order_by("year", "month")

        result = await db.execute(stmt)
        rows = result.fetchall()

        trend = []
        for row in rows:
            trend.append({
                "month": f"{int(row.year)}-{int(row.month):02d}",
                "revenue": round(float(row.revenue), 2) if row.revenue else 0,
                "direct": round(float(row.direct_revenue), 2) if row.direct_revenue else 0,
                "ota": round(float(row.revenue or 0) - float(row.direct_revenue or 0), 2),
            })
        return trend[-months:]

    async def get_occupancy_trend(self, months: int, db: AsyncSession) -> List[dict]:
        """Get monthly occupancy trend."""
        from sqlalchemy import extract
        stmt = select(
            extract("year", PricingHistory.date).label("year"),
            extract("month", PricingHistory.date).label("month"),
            func.avg(PricingHistory.occupancy_rate).label("avg_occupancy"),
        ).group_by("year", "month").order_by("year", "month")

        result = await db.execute(stmt)
        rows = result.fetchall()

        return [
            {
                "month": f"{int(r.year)}-{int(r.month):02d}",
                "occupancy_rate": round(float(r.avg_occupancy), 4),
            }
            for r in rows[-months:]
        ]

    async def get_current_multipliers(self, target_date: date, db: AsyncSession) -> dict:
        """Get current pricing multipliers."""
        return {
            "season": self._season_multiplier(target_date),
            "urgency": self._urgency_multiplier(target_date),
            "event": await self._event_multiplier(target_date, db),
            "date": target_date.isoformat(),
        }
