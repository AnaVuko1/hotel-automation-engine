"""HAES application configuration via pydantic-settings"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/hotel.db"

    # Security
    SECRET_KEY: str = "change-this-to-a-random-secret-in-production"

    # Redis (optional)
    REDIS_URL: Optional[str] = None

    # Hotel Configuration
    HOTEL_NAME: str = "Grand Horizon Hotel"
    HOTEL_ADDRESS: str = "123 Ocean Boulevard, Miami, FL 33139"
    HOTEL_PHONE: str = "+1-305-555-0123"
    HOTEL_EMAIL: str = "info@grandhorizonhotel.com"
    HOTEL_DESCRIPTION: str = "A luxurious beachfront hotel with stunning ocean views and premium amenities."
    HOTEL_TOTAL_ROOMS: int = 120
    HOTEL_CHECK_IN: str = "15:00"
    HOTEL_CHECK_OUT: str = "11:00"

    # Pricing defaults
    OTA_COMMISSION_RATE: float = 0.18
    BASE_PRICE_STANDARD: int = 120
    BASE_PRICE_DELUXE: int = 195
    BASE_PRICE_SUITE: int = 310

    # Multiplier bounds
    OCCUPANCY_MULT_MIN: float = 0.8
    OCCUPANCY_MULT_MAX: float = 1.4
    SEASON_MULT_MIN: float = 0.7
    SEASON_MULT_MAX: float = 1.3
    URGENCY_MULT_MIN: float = 0.9
    URGENCY_MULT_MAX: float = 1.5
    EVENT_MULT_MIN: float = 0.8
    EVENT_MULT_MAX: float = 1.6

    # Agent toggles
    GUEST_AGENT_ENABLED: bool = True
    OPS_AGENT_ENABLED: bool = True
    HSK_AGENT_ENABLED: bool = True
    REVENUE_AGENT_ENABLED: bool = True

    # Escalation contacts
    ESCALATION_EMAIL: str = "manager@grandhorizonhotel.com"
    ESCALATION_PHONE: str = "+1-305-555-0199"

    # Dashboard
    DASHBOARD_REFRESH_INTERVAL: int = 300  # seconds

    class Config:
        env_file = ".env"


settings = Settings()
