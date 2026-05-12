"""SQLAlchemy models for Hotel Automation Engine"""
from datetime import date, datetime, timedelta
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text, Date, JSON, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


# ─── Enums ───────────────────────────────────────────────────────────────────

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class MessageChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


# ─── Core Hotel Models ───────────────────────────────────────────────────────

class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    total_rooms = Column(Integer, default=0)
    check_in_time = Column(String(10), default="15:00")
    check_out_time = Column(String(10), default="11:00")
    ai_readiness_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    room_types = relationship("RoomType", back_populates="hotel", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="hotel", cascade="all, delete-orphan")
    pricing_history = relationship("PricingHistory", back_populates="hotel", cascade="all, delete-orphan")
    maintenance_tasks = relationship("MaintenanceTask", back_populates="hotel", cascade="all, delete-orphan")
    housekeeping_tasks = relationship("HousekeepingTask", back_populates="hotel", cascade="all, delete-orphan")
    guest_messages = relationship("GuestMessage", back_populates="hotel", cascade="all, delete-orphan")


class RoomType(Base):
    __tablename__ = "room_types"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    base_price = Column(Float, nullable=False)
    capacity = Column(Integer, default=2)
    total_count = Column(Integer, default=0)
    amenities = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    hotel = relationship("Hotel", back_populates="room_types")
    bookings = relationship("Booking", back_populates="room_type", cascade="all, delete-orphan")
    pricing_history = relationship("PricingHistory", back_populates="room_type", cascade="all, delete-orphan")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    room_type_id = Column(Integer, ForeignKey("room_types.id"), nullable=False)
    room_number = Column(String(10), nullable=True)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    guest_name = Column(String(255), nullable=False)
    guest_email = Column(String(255), nullable=False)
    guest_phone = Column(String(50), nullable=True)
    total_price = Column(Float, nullable=False)
    commission_paid = Column(Float, default=0.0)
    is_direct_booking = Column(Boolean, default=True)
    booking_source = Column(String(100), default="Direct")
    status = Column(String(50), default=BookingStatus.CONFIRMED.value)
    special_requests = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hotel = relationship("Hotel", back_populates="bookings")
    room_type = relationship("RoomType", back_populates="bookings")


class PricingHistory(Base):
    __tablename__ = "pricing_history"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    room_type_id = Column(Integer, ForeignKey("room_types.id"), nullable=False)
    date = Column(Date, nullable=False)
    base_price = Column(Float, nullable=False)
    final_price = Column(Float, nullable=False)
    occupancy_mult = Column(Float, default=1.0)
    season_mult = Column(Float, default=1.0)
    urgency_mult = Column(Float, default=1.0)
    event_mult = Column(Float, default=1.0)
    occupancy_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    hotel = relationship("Hotel", back_populates="pricing_history")
    room_type = relationship("RoomType", back_populates="pricing_history")


class LocalEvent(Base):
    __tablename__ = "local_events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    event_date = Column(Date, nullable=False)
    impact_multiplier = Column(Float, default=1.0)
    category = Column(String(100), default="general")
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Agent Operation Models ──────────────────────────────────────────────────

class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    room_number = Column(String(10), nullable=True)
    category = Column(String(100), default="general")  # plumbing, electrical, hvac, etc.
    priority = Column(String(20), default=TaskPriority.MEDIUM.value)
    status = Column(String(20), default=TaskStatus.PENDING.value)
    assigned_to = Column(String(100), nullable=True)
    reported_by = Column(String(100), default="guest")
    source = Column(String(50), default="guest_request")  # guest_request, hsk_report, scheduled
    estimated_minutes = Column(Integer, default=30)
    resolution_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    hotel = relationship("Hotel", back_populates="maintenance_tasks")


class HousekeepingTask(Base):
    __tablename__ = "housekeeping_tasks"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    room_number = Column(String(10), nullable=False)
    task_type = Column(String(50), default="full_clean")  # full_clean, turndown, deep_clean, touch_up
    status = Column(String(20), default=TaskStatus.PENDING.value)
    priority = Column(String(20), default=TaskPriority.MEDIUM.value)
    assigned_to = Column(String(100), nullable=True)
    notes = Column(Text, default="")
    is_checkout_clean = Column(Boolean, default=False)
    is_stayover_clean = Column(Boolean, default=False)
    scheduled_time = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hotel = relationship("Hotel", back_populates="housekeeping_tasks")


class GuestMessage(Base):
    __tablename__ = "guest_messages"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    guest_name = Column(String(255), nullable=False)
    guest_email = Column(String(255), nullable=True)
    guest_phone = Column(String(50), nullable=True)
    channel = Column(String(50), default=MessageChannel.EMAIL.value)
    direction = Column(String(20), default=MessageDirection.OUTBOUND.value)
    subject = Column(String(255), default="")
    body = Column(Text, nullable=False)
    agent_type = Column(String(50), default="guest")  # which agent handled it
    auto_generated = Column(Boolean, default=True)
    sentiment = Column(String(20), nullable=True)  # positive, neutral, negative
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    hotel = relationship("Hotel", back_populates="guest_messages")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_type = Column(String(50), nullable=False)  # orchestrator, guest, ops, hsk, revenue
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)  # booking, task, message, price
    entity_id = Column(Integer, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    decision = Column(String(50), nullable=True)  # auto, escalated, scheduled
    confidence = Column(Float, default=1.0)
    duration_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
