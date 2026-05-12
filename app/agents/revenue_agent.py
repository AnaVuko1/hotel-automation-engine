"""Revenue Agent — dynamic pricing, yield management, forecasting"""
from datetime import date, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.agents.base import BaseAgent
from app.services.pricing_engine import PricingEngine
from app.models import RoomType, PricingHistory, Booking, LocalEvent


class RevenueAgent(BaseAgent):
    """Dynamic pricing and revenue optimization agent."""

    def __init__(self):
        super().__init__("revenue")
        self.pricing_engine = PricingEngine()

    async def handle_pricing(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Recalculate pricing for a specific date."""
        target_date = params.get("date")
        if isinstance(target_date, str):
            from datetime import date as dt_date
            target_date = dt_date.fromisoformat(target_date)
        if not target_date:
            target_date = date.today()

        result = await self.pricing_engine.recalculate_pricing(target_date, db)

        # Persist to pricing history
        room_types_stmt = select(RoomType)
        rt_result = await db.execute(room_types_stmt)
        room_types = rt_result.scalars().all()

        for rt in room_types:
            try:
                final_price = await self.pricing_engine.calculate_price(rt.id, target_date, db)
                occupancy_mult = await self.pricing_engine._occupancy_multiplier(rt.id, target_date, db)
                event_mult = await self.pricing_engine._event_multiplier(target_date, db)

                # Calculate occupancy rate
                total_stmt = select(func.count()).select_from(Booking).where(
                    and_(
                        Booking.room_type_id == rt.id,
                        Booking.check_in_date <= target_date,
                        Booking.check_out_date > target_date,
                        Booking.status.in_(["confirmed", "checked_in"]),
                    )
                )
                booked_result = await db.execute(total_stmt)
                booked = booked_result.scalar() or 0
                occ_rate = booked / rt.total_count if rt.total_count > 0 else 0

                ph = PricingHistory(
                    hotel_id=rt.hotel_id,
                    room_type_id=rt.id,
                    date=target_date,
                    base_price=rt.base_price,
                    final_price=final_price,
                    occupancy_mult=occupancy_mult,
                    season_mult=self.pricing_engine._season_multiplier(target_date),
                    urgency_mult=self.pricing_engine._urgency_multiplier(target_date),
                    event_mult=event_mult,
                    occupancy_rate=occ_rate,
                )
                db.add(ph)
            except Exception:
                continue

        await db.commit()

        return {
            "status": "completed",
            "result": result,
            "confidence": 0.95,
            "message": f"Pricing recalculated for {target_date.isoformat()}",
            "decision": "auto",
        }

    async def handle_forecast(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Generate a revenue forecast for upcoming days."""
        days = params.get("days", 30)
        start_date = date.today()
        end_date = start_date + timedelta(days=days)

        stmt = select(RoomType)
        result = await db.execute(stmt)
        room_types = result.scalars().all()

        forecast = []
        current = start_date
        while current < end_date:
            day_data = {"date": current.isoformat(), "rooms": []}
            for rt in room_types:
                try:
                    price = await self.pricing_engine.calculate_price(rt.id, current, db)
                    day_data["rooms"].append({
                        "room_type": rt.name,
                        "price": price,
                    })
                except Exception:
                    day_data["rooms"].append({
                        "room_type": rt.name,
                        "price": rt.base_price,
                    })
            forecast.append(day_data)
            current += timedelta(days=1)

        return {
            "status": "completed",
            "result": {
                "forecast_days": days,
                "start_date": start_date.isoformat(),
                "forecast": forecast,
            },
            "confidence": 0.85,
            "message": f"Forecast generated for {days} days",
            "decision": "auto",
        }

    async def handle_events(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Get upcoming local events that affect pricing."""
        target_date = params.get("date")
        if isinstance(target_date, str):
            from datetime import date as dt_date
            target_date = dt_date.fromisoformat(target_date)
        if not target_date:
            target_date = date.today()

        stmt = select(LocalEvent).where(
            LocalEvent.event_date >= target_date
        ).order_by(LocalEvent.event_date).limit(20)

        result = await db.execute(stmt)
        events = result.scalars().all()

        return {
            "status": "completed",
            "result": {
                "events": [
                    {
                        "id": e.id,
                        "name": e.name,
                        "date": e.event_date.isoformat(),
                        "category": e.category,
                        "impact": e.impact_multiplier,
                    }
                    for e in events
                ]
            },
            "confidence": 1.0,
            "message": f"Found {len(events)} upcoming events",
            "decision": "auto",
        }

    async def handle_report(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Generate a revenue report for a date range."""
        end_date = date.today()
        start_date = end_date - timedelta(days=params.get("days", 30))

        metrics = await self._compute_metrics(start_date, end_date, db)

        return {
            "status": "completed",
            "result": metrics,
            "confidence": 0.9,
            "message": f"Revenue report generated for {start_date.isoformat()} to {end_date.isoformat()}",
            "decision": "auto",
        }

    async def _compute_metrics(self, start_date: date, end_date: date, db: AsyncSession) -> Dict[str, Any]:
        """Compute revenue metrics for a date range."""
        try:
            total_revenue = await self.pricing_engine.calculate_total_revenue(start_date, end_date, db)
        except Exception:
            total_revenue = 0
        try:
            adr = await self.pricing_engine.calculate_average_daily_rate(start_date, end_date, db)
        except Exception:
            adr = 0
        try:
            occ = await self.pricing_engine.calculate_occupancy_rate(start_date, end_date, db)
        except Exception:
            occ = 0
        try:
            revpar = await self.pricing_engine.calculate_revpar(start_date, end_date, db)
        except Exception:
            revpar = 0

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_revenue": round(total_revenue, 2),
            "average_daily_rate": round(adr, 2),
            "occupancy_rate": round(occ, 4),
            "revpar": round(revpar, 2),
        }
