#!/usr/bin/env python3
"""Seed the database with realistic hotel demo data — 12 months of operations."""
import asyncio
import random
import sys
import os
from datetime import date, timedelta, datetime
from pathlib import Path

# Ensure we can import from app
sys.path.insert(0, str(Path(__file__).parent))

random.seed(42)


async def seed_database():
    """Seed with realistic hotel data."""
    from app.database import AsyncSessionLocal, init_db
    from app.models import Hotel, RoomType, Booking, PricingHistory, LocalEvent, \
        MaintenanceTask, HousekeepingTask, GuestMessage
    from app.services.pricing_engine import PricingEngine

    await init_db()
    engine = PricingEngine()

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        from sqlalchemy import select, func
        existing = await db.execute(select(func.count()).select_from(Hotel))
        if existing.scalar() and existing.scalar() > 0:
            print("Database already seeded. Skipping.")
            return

        # ── Hotel ────────────────────────────────────────────────────────────
        hotel = Hotel(
            name="Grand Horizon Hotel",
            address="123 Ocean Boulevard, Miami, FL 33139",
            phone="+1-305-555-0123",
            email="info@grandhorizonhotel.com",
            description="A luxurious beachfront hotel with stunning ocean views, world-class dining, "
                       "and premium amenities. 120 rooms across 12 floors with full spa and conference facilities.",
            total_rooms=120,
            check_in_time="15:00",
            check_out_time="11:00",
        )
        db.add(hotel)
        await db.flush()

        # ── Room Types ───────────────────────────────────────────────────────
        rooms_data = [
            {"name": "Standard Room", "desc": "Comfortable room with ocean view, queen bed.",
             "price": 120, "cap": 2, "count": 60,
             "amenities": ["Ocean View", "Air Conditioning", "Mini Bar", "Safe", "Flat Screen TV",
                          "Free WiFi", "Work Desk"]},
            {"name": "Deluxe Room", "desc": "Spacious room with private balcony and king bed.",
             "price": 195, "cap": 3, "count": 40,
             "amenities": ["Ocean View", "Balcony", "Jacuzzi", "Air Conditioning", "Mini Bar",
                          "Safe", "Flat Screen TV", "Free WiFi", "Espresso Machine", "Bathrobe"]},
            {"name": "Suite", "desc": "Premium corner suite with panoramic views, separate living area.",
             "price": 310, "cap": 4, "count": 20,
             "amenities": ["Panoramic View", "Living Room", "Kitchenette", "Jacuzzi", "Butler Service",
                          "Air Conditioning", "Mini Bar", "Safe", "Flat Screen TV", "Walk-in Closet",
                          "Free WiFi", "Espresso Machine", "Bathrobe", "Slippers"]},
        ]

        room_types = []
        for r in rooms_data:
            rt = RoomType(
                hotel_id=hotel.id,
                name=r["name"],
                description=r["desc"],
                base_price=r["price"],
                capacity=r["cap"],
                total_count=r["count"],
                amenities=r["amenities"],
            )
            db.add(rt)
            room_types.append(rt)
        await db.flush()

        # ── Local Events ──────────────────────────────────────────────────────
        events = [
            ("Miami Art Week", "Annual art fair with international galleries", "2025-12-03", 1.6, "conference"),
            ("New Year's Eve Gala", "Grand celebration with fireworks", "2025-12-31", 1.7, "festival"),
            ("Miami Marathon", "International marathon through the city", "2026-01-25", 1.3, "sports"),
            ("Spring Break", "Peak spring travel season", "2026-03-15", 1.4, "seasonal"),
            ("Jazz Festival", "Three-day waterfront jazz festival", "2026-04-10", 1.3, "festival"),
            ("Tech Summit", "Annual technology leadership conference", "2026-05-12", 1.4, "conference"),
            ("Summer Kickoff", "Official start of summer season", "2026-06-01", 1.3, "seasonal"),
            ("Independence Day", "Fourth of July celebrations", "2026-07-04", 1.5, "festival"),
            ("Food & Wine Festival", "Culinary showcase with top chefs", "2026-08-21", 1.35, "festival"),
            ("Labor Day Weekend", "End of summer holiday weekend", "2026-09-04", 1.4, "seasonal"),
            ("Tech Conference", "Major industry conference", "2026-10-14", 1.5, "conference"),
            ("Thanksgiving Weekend", "Holiday family travel", "2026-11-26", 1.3, "seasonal"),
            ("Christmas Market", "Holiday market and festivities", "2026-12-15", 1.5, "festival"),
        ]

        for name, desc, d, mult, cat in events:
            event = LocalEvent(
                name=name, description=desc,
                event_date=date.fromisoformat(d),
                impact_multiplier=mult, category=cat,
            )
            db.add(event)

        # ── Bookings (12 months of history + future reservations) ─────────────
        today = date.today()
        base_season_mult = {
            1: 0.9, 2: 0.9, 3: 1.1, 4: 1.0, 5: 1.0, 6: 1.2,
            7: 1.2, 8: 1.1, 9: 0.9, 10: 0.95, 11: 0.85, 12: 1.3,
        }
        start = today - timedelta(days=365)
        end = today + timedelta(days=180)

        guest_pool = [
            ("John Smith", "john.smith@email.com", "+1-305-555-1001"),
            ("Sarah Johnson", "sarah.j@email.com", "+1-305-555-1002"),
            ("Michael Chen", "m.chen@email.com", "+1-305-555-1003"),
            ("Emma Williams", "emma.w@email.com", "+1-305-555-1004"),
            ("James Brown", "j.brown@email.com", "+1-305-555-1005"),
            ("Maria Garcia", "maria.g@email.com", "+1-305-555-1006"),
            ("David Miller", "d.miller@email.com", "+1-305-555-1007"),
            ("Lisa Anderson", "l.anderson@email.com", "+1-305-555-1008"),
            ("Robert Taylor", "r.taylor@email.com", "+1-305-555-1009"),
            ("Jennifer Thomas", "j.thomas@email.com", "+1-305-555-1010"),
            ("Christopher Lee", "c.lee@email.com", "+1-305-555-1011"),
            ("Amanda White", "a.white@email.com", "+1-305-555-1012"),
            ("Daniel Martinez", "d.martinez@email.com", "+1-305-555-1013"),
            ("Michelle Robinson", "m.robinson@email.com", "+1-305-555-1014"),
            ("Kevin Clark", "k.clark@email.com", "+1-305-555-1015"),
            ("Rachel Harris", "r.harris@email.com", "+1-305-555-1016"),
            ("Brian Lewis", "b.lewis@email.com", "+1-305-555-1017"),
            ("Stephanie Walker", "s.walker@email.com", "+1-305-555-1018"),
            ("Andrew Hall", "a.hall@email.com", "+1-305-555-1019"),
            ("Nicole Young", "n.young@email.com", "+1-305-555-1020"),
        ]

        bookings_created = 0
        current = start
        while current < end:
            # Determine occupancy probability for this month
            month = current.month
            season_factor = base_season_mult.get(month, 1.0)
            is_weekend = current.weekday() >= 5

            # Number of new bookings for this day
            base_prob = 0.6 if is_weekend else 0.4
            daily_prob = base_prob * season_factor

            if random.random() < daily_prob:
                num_bookings = random.choices([1, 2, 3, 4], weights=[40, 30, 20, 10])[0]
                for _ in range(num_bookings):
                    if random.random() > 0.3:  # 70% chance of booking per slot
                        rt = random.choice(room_types)
                        guest = random.choice(guest_pool)
                        nights = random.choices([1, 2, 3, 4, 5, 7, 10], weights=[20, 30, 20, 15, 8, 5, 2])[0]

                        is_direct = random.random() > 0.35  # 65% direct

                        status_weights = {"confirmed": 60, "checked_in": 15, "checked_out": 20, "cancelled": 5}
                        if current > today:
                            status_weights = {"confirmed": 90, "cancelled": 10}
                        elif current < today - timedelta(days=3):
                            status_weights = {"checked_out": 85, "checked_in": 5, "cancelled": 10}

                        status = random.choices(
                            list(status_weights.keys()),
                            weights=list(status_weights.values()),
                        )[0]

                        total_price = rt.base_price * nights
                        commission = total_price * 0.18 if not is_direct else 0

                        booking = Booking(
                            hotel_id=hotel.id,
                            room_type_id=rt.id,
                            check_in_date=current,
                            check_out_date=current + timedelta(days=nights),
                            guest_name=guest[0],
                            guest_email=guest[1],
                            guest_phone=guest[2],
                            total_price=round(total_price, 2),
                            commission_paid=round(commission, 2),
                            is_direct_booking=is_direct,
                            booking_source="Direct" if is_direct else random.choice(
                                ["Booking.com", "Expedia", "Agoda", "Hotels.com"]
                            ),
                            status=status,
                        )
                        db.add(booking)
                        bookings_created += 1

            current += timedelta(days=1)

        await db.flush()
        print(f"Created {bookings_created} bookings")

        # ── Pricing History ───────────────────────────────────────────────────
        ph_created = 0
        ph_start = today - timedelta(days=365)
        ph_end = today + timedelta(days=90)
        ph_current = ph_start
        while ph_current < ph_end:
            for rt in room_types:
                try:
                    final_price = await engine.calculate_price(rt.id, ph_current, db)
                except Exception:
                    final_price = rt.base_price

                occ = random.uniform(0.15, 0.95)
                ph = PricingHistory(
                    hotel_id=hotel.id,
                    room_type_id=rt.id,
                    date=ph_current,
                    base_price=rt.base_price,
                    final_price=round(final_price, 2),
                    occupancy_mult=random.uniform(0.8, 1.4),
                    season_mult=engine._season_multiplier(ph_current),
                    urgency_mult=random.uniform(0.9, 1.5),
                    event_mult=random.uniform(0.9, 1.3),
                    occupancy_rate=round(occ, 4),
                )
                db.add(ph)
                ph_created += 1
            ph_current += timedelta(days=1)
        print(f"Created {ph_created} pricing history records")

        # ── Sample Maintenance Tasks ─────────────────────────────────────────
        maint_tasks = [
            ("AC not cooling in 1204", "Guest reported AC not working", "1204", "hvac", "high"),
            ("Leaky faucet in 805", "Slow drip from bathroom sink", "805", "plumbing", "medium"),
            ("Light bulb out in corridor", "3rd floor hallway needs bulb replacement", None, "general", "low"),
            ("Pool pump maintenance", "Scheduled pool filter cleaning", None, "general", "medium"),
            ("Elevator inspection", "Annual safety inspection due", None, "general", "medium"),
        ]
        for title, desc, room, cat, pri in maint_tasks:
            task = MaintenanceTask(
                hotel_id=hotel.id, title=title, description=desc,
                room_number=room, category=cat, priority=pri,
                status="pending", source="guest_request",
            )
            db.add(task)

        # ── Sample Housekeeping Tasks ─────────────────────────────────────────
        for room_num in ["1204", "805", "607", "312", "1501"]:
            task = HousekeepingTask(
                hotel_id=hotel.id, room_number=room_num,
                task_type="full_clean", status="pending",
                is_checkout_clean=room_num in ["1204", "607"],
            )
            db.add(task)

        # ── Sample Guest Messages ─────────────────────────────────────────────
        welcome_msgs = [
            ("John Smith", "john.smith@email.com",
             "Welcome to Grand Horizon Hotel!",
             "Dear John, welcome! Your room 1204 is ready. Enjoy your stay!"),
            ("Sarah Johnson", "sarah.j@email.com",
             "Your stay at Grand Horizon",
             "Dear Sarah, thank you for choosing Grand Horizon. Check-in: 3PM."),
        ]
        for name, email, subj, body in welcome_msgs:
            msg = GuestMessage(
                hotel_id=hotel.id, guest_name=name,
                guest_email=email, channel="email",
                direction="outbound", subject=subj, body=body,
                agent_type="guest", auto_generated=True,
            )
            db.add(msg)

        await db.commit()

        print(f"\n✅ Seeding complete!")
        print(f"   Hotel: {hotel.name}")
        print(f"   Room types: {len(room_types)} ({sum(r.total_count for r in room_types)} total rooms)")
        print(f"   Bookings: {bookings_created}")
        print(f"   Pricing records: {ph_created}")
        print(f"   Events: {len(events)}")


if __name__ == "__main__":
    asyncio.run(seed_database())
