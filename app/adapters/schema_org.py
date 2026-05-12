"""Schema.org JSON-LD generator for AI agent discovery"""
from datetime import date, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.config import settings
from app.schemas import SchemaOrgHotel, SchemaOrgRoom, SchemaOrgAvailability
from app.models import RoomType, Booking


def generate_hotel_jsonld() -> SchemaOrgHotel:
    """Generate schema.org Hotel JSON-LD for AI agent discovery."""
    return SchemaOrgHotel(
        name=settings.HOTEL_NAME,
        description=settings.HOTEL_DESCRIPTION,
        address={
            "@type": "PostalAddress",
            "streetAddress": settings.HOTEL_ADDRESS.split(",")[0].strip(),
            "addressLocality": settings.HOTEL_ADDRESS.split(",")[1].strip() if "," in settings.HOTEL_ADDRESS else "",
            "addressRegion": "FL",
            "postalCode": "33139",
            "addressCountry": "US",
        },
        telephone=settings.HOTEL_PHONE,
        email=settings.HOTEL_EMAIL,
        checkinTime=settings.HOTEL_CHECK_IN,
        checkoutTime=settings.HOTEL_CHECK_OUT,
        priceRange="$$$",
        amenities=[
            "Free WiFi", "Swimming Pool", "Fitness Center",
            "Spa", "Restaurant", "Bar", "Conference Facilities",
            "Room Service", "Beach Access", "Valet Parking",
        ],
    )


def generate_rooms_jsonld() -> List[SchemaOrgRoom]:
    """Generate schema.org Room JSON-LD for all room types."""
    return [
        SchemaOrgRoom(
            name="Standard Room",
            description="Comfortable room with ocean view, perfect for couples or solo travelers.",
            bed={"@type": "BedDetails", "numberOfBeds": 1, "bedType": "Queen"},
            occupancy={"@type": "QuantitativeValue", "minValue": 1, "maxValue": 2},
            priceSpecification={
                "@type": "UnitPriceSpecification",
                "priceCurrency": "USD",
                "price": settings.BASE_PRICE_STANDARD,
                "unitCode": "DAY",
            },
            amenities=["Ocean View", "Air Conditioning", "Mini Bar", "Safe", "Flat Screen TV"],
        ),
        SchemaOrgRoom(
            name="Deluxe Room",
            description="Spacious room with balcony and premium amenities.",
            bed={"@type": "BedDetails", "numberOfBeds": 1, "bedType": "King"},
            occupancy={"@type": "QuantitativeValue", "minValue": 1, "maxValue": 3},
            priceSpecification={
                "@type": "UnitPriceSpecification",
                "priceCurrency": "USD",
                "price": settings.BASE_PRICE_DELUXE,
                "unitCode": "DAY",
            },
            amenities=["Ocean View", "Balcony", "Jacuzzi", "Air Conditioning", "Mini Bar", "Safe", "Flat Screen TV"],
        ),
        SchemaOrgRoom(
            name="Suite",
            description="Premium suite with separate living area and panoramic views.",
            bed={"@type": "BedDetails", "numberOfBeds": 1, "bedType": "King"},
            occupancy={"@type": "QuantitativeValue", "minValue": 1, "maxValue": 4},
            priceSpecification={
                "@type": "UnitPriceSpecification",
                "priceCurrency": "USD",
                "price": settings.BASE_PRICE_SUITE,
                "unitCode": "DAY",
            },
            amenities=["Panoramic View", "Living Room", "Kitchenette", "Jacuzzi", "Butler Service",
                       "Air Conditioning", "Mini Bar", "Safe", "Flat Screen TV", "Walk-in Closet"],
        ),
    ]


async def generate_availability_jsonld(
    checkin: date, checkout: date, db: AsyncSession
) -> List[SchemaOrgAvailability]:
    """Generate schema.org Offer (availability) JSON-LD."""
    from app.services.pricing_engine import PricingEngine
    engine = PricingEngine()
    availabilities = []

    stmt = select(RoomType)
    result = await db.execute(stmt)
    room_types = result.scalars().all()

    for rt in room_types:
        current_date = checkin
        while current_date < checkout:
            try:
                price = await engine.calculate_price(rt.id, current_date, db)
            except Exception:
                price = rt.base_price

            # Count booked rooms for this date
            count_stmt = select(func.count()).select_from(Booking).where(
                and_(
                    Booking.room_type_id == rt.id,
                    Booking.check_in_date <= current_date,
                    Booking.check_out_date > current_date,
                    Booking.status.in_(["confirmed", "checked_in"]),
                )
            )
            count_result = await db.execute(count_stmt)
            booked = count_result.scalar() or 0
            available = booked < rt.total_count

            availabilities.append(SchemaOrgAvailability(
                name=f"{rt.name} - {current_date.isoformat()}",
                price=round(price, 2),
                priceCurrency="USD",
                availability="https://schema.org/InStock" if available else "https://schema.org/SoldOut",
                availabilityStarts=current_date,
                availabilityEnds=current_date,
                eligibleRegion={"@type": "Country", "name": "US"},
            ))
            current_date += timedelta(days=1)

    return availabilities


def validate_schema_compliance() -> dict:
    """Validate schema.org compliance. Returns score and validity."""
    try:
        hotel = generate_hotel_jsonld()
        rooms = generate_rooms_jsonld()
        is_valid = bool(hotel.name and rooms)
        return {
            "valid": is_valid,
            "score": 40 if is_valid else 0,
            "hotel_ld": hotel.model_dump(by_alias=True) if is_valid else None,
            "room_count": len(rooms),
        }
    except Exception as e:
        return {"valid": False, "score": 0, "error": str(e)}
