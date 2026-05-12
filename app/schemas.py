"""Pydantic schemas for request/response validation"""
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


# ─── Hotel ───────────────────────────────────────────────────────────────────

class HotelBase(BaseModel):
    name: str = Field(..., max_length=255)
    address: str = Field(..., max_length=500)
    phone: str = Field(..., max_length=50)
    email: EmailStr
    description: str
    total_rooms: int = Field(default=0, ge=0)
    check_in_time: str = Field(default="15:00")
    check_out_time: str = Field(default="11:00")


class HotelCreate(HotelBase):
    pass


class HotelUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    description: Optional[str] = None
    total_rooms: Optional[int] = Field(None, ge=0)


class HotelResponse(HotelBase):
    id: int
    ai_readiness_score: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Room Type ───────────────────────────────────────────────────────────────

class RoomTypeBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str
    base_price: float = Field(..., gt=0)
    capacity: int = Field(default=2, ge=1)
    total_count: int = Field(default=0, ge=0)
    amenities: list = Field(default_factory=list)


class RoomTypeCreate(RoomTypeBase):
    hotel_id: int


class RoomTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = Field(None, gt=0)
    capacity: Optional[int] = Field(None, ge=1)
    total_count: Optional[int] = Field(None, ge=0)
    amenities: Optional[List[str]] = None


class RoomTypeResponse(RoomTypeBase):
    id: int
    hotel_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Booking ─────────────────────────────────────────────────────────────────

class BookingBase(BaseModel):
    check_in_date: date
    check_out_date: date
    guest_name: str = Field(..., max_length=255)
    guest_email: EmailStr
    guest_phone: Optional[str] = None
    total_price: float = Field(..., gt=0)
    commission_paid: float = Field(default=0.0, ge=0)
    is_direct_booking: bool = Field(default=True)
    booking_source: str = Field(default="Direct", max_length=100)
    status: str = Field(default="confirmed", max_length=50)
    special_requests: str = Field(default="")


class BookingCreate(BookingBase):
    hotel_id: int
    room_type_id: int


class BookingUpdate(BaseModel):
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    room_number: Optional[str] = None
    guest_name: Optional[str] = None
    guest_email: Optional[EmailStr] = None
    guest_phone: Optional[str] = None
    total_price: Optional[float] = Field(None, gt=0)
    commission_paid: Optional[float] = Field(None, ge=0)
    is_direct_booking: Optional[bool] = None
    booking_source: Optional[str] = None
    status: Optional[str] = None
    special_requests: Optional[str] = None


class BookingResponse(BookingBase):
    id: int
    hotel_id: int
    room_type_id: int
    room_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CheckInRequest(BaseModel):
    booking_id: int
    room_number: str = Field(..., max_length=10)
    id_document: Optional[str] = None
    special_notes: Optional[str] = None


class CheckOutRequest(BaseModel):
    booking_id: int
    final_bill_adjustments: Optional[float] = None
    feedback: Optional[str] = None


class UpsellRequest(BaseModel):
    booking_id: int
    offer_type: str = Field(..., description="room_upgrade, late_checkout, spa, dining")
    offer_details: Dict[str, Any] = Field(default_factory=dict)


# ─── Pricing ─────────────────────────────────────────────────────────────────

class PricingHistoryBase(BaseModel):
    date: date
    base_price: float = Field(..., gt=0)
    final_price: float = Field(..., gt=0)
    occupancy_mult: float = Field(default=1.0, gt=0)
    season_mult: float = Field(default=1.0, gt=0)
    urgency_mult: float = Field(default=1.0, gt=0)
    event_mult: float = Field(default=1.0, gt=0)
    occupancy_rate: float = Field(default=0.0, ge=0, le=1.0)


class PricingHistoryResponse(PricingHistoryBase):
    id: int
    hotel_id: int
    room_type_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Local Events ────────────────────────────────────────────────────────────

class LocalEventBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str
    event_date: date
    impact_multiplier: float = Field(default=1.0, gt=0)
    category: str = Field(default="general", max_length=100)


class LocalEventCreate(LocalEventBase):
    pass


class LocalEventResponse(LocalEventBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Maintenance ─────────────────────────────────────────────────────────────

class MaintenanceTaskCreate(BaseModel):
    hotel_id: int
    title: str = Field(..., max_length=255)
    description: str = ""
    room_number: Optional[str] = None
    category: str = "general"
    priority: str = "medium"
    source: str = "guest_request"
    estimated_minutes: int = 30
    reported_by: str = "guest"


class MaintenanceTaskUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    resolution_notes: Optional[str] = None
    estimated_minutes: Optional[int] = None


class MaintenanceTaskResponse(BaseModel):
    id: int
    hotel_id: int
    title: str
    description: str
    room_number: Optional[str]
    category: str
    priority: str
    status: str
    assigned_to: Optional[str]
    reported_by: str
    source: str
    estimated_minutes: int
    resolution_notes: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Housekeeping ────────────────────────────────────────────────────────────

class HousekeepingTaskCreate(BaseModel):
    hotel_id: int
    room_number: str = Field(..., max_length=10)
    task_type: str = "full_clean"
    priority: str = "medium"
    notes: str = ""
    is_checkout_clean: bool = False
    is_stayover_clean: bool = False


class HousekeepingTaskUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    priority: Optional[str] = None


class HousekeepingTaskResponse(BaseModel):
    id: int
    hotel_id: int
    room_number: str
    task_type: str
    status: str
    priority: str
    assigned_to: Optional[str]
    notes: str
    is_checkout_clean: bool
    is_stayover_clean: bool
    scheduled_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Guest Messaging ─────────────────────────────────────────────────────────

class GuestMessageCreate(BaseModel):
    hotel_id: int
    booking_id: Optional[int] = None
    guest_name: str
    guest_email: Optional[str] = None
    guest_phone: Optional[str] = None
    channel: str = "email"
    direction: str = "outbound"
    subject: str = ""
    body: str
    agent_type: str = "guest"
    auto_generated: bool = True


class GuestMessageResponse(BaseModel):
    id: int
    hotel_id: int
    booking_id: Optional[int]
    guest_name: str
    guest_email: Optional[str]
    guest_phone: Optional[str]
    channel: str
    direction: str
    subject: str
    body: str
    agent_type: str
    auto_generated: bool
    sentiment: Optional[str]
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Agent Orchestration ────────────────────────────────────────────────────

class AgentActionRequest(BaseModel):
    """Generic request to trigger an agent action."""
    agent: str = Field(..., description="guest|ops|hsk|revenue|orchestrator")
    action: str = Field(..., description="action name")
    params: Dict[str, Any] = Field(default_factory=dict)


class AgentActionResponse(BaseModel):
    agent: str
    action: str
    status: str  # completed, escalated, scheduled, error
    result: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    duration_ms: int = 0
    message: str = ""


class AgentLogResponse(BaseModel):
    id: int
    agent_type: str
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    decision: Optional[str]
    confidence: float
    duration_ms: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Analytics / Dashboard ──────────────────────────────────────────────────

class DashboardMetrics(BaseModel):
    occupancy_rate: float
    average_daily_rate: float
    revpar: float
    total_revenue: float
    direct_booking_rate: float
    ota_leakage: float
    ai_readiness_score: int
    active_maintenance: int
    pending_housekeeping: int
    check_ins_today: int
    check_outs_today: int


class RevenueTrend(BaseModel):
    month: str
    revenue: float
    direct: float
    ota: float


class AgentPerformance(BaseModel):
    agent: str
    actions_taken: int
    auto_resolved: int
    escalated: int
    avg_duration_ms: int
    success_rate: float


# ─── Schema.org AI Discovery ─────────────────────────────────────────────────

class SchemaOrgHotel(BaseModel):
    context: str = Field(default="https://schema.org", alias="@context")
    type: str = Field(default="Hotel", alias="@type")
    name: str
    description: str
    address: Dict[str, Any]
    telephone: str
    email: str
    checkinTime: str
    checkoutTime: str
    priceRange: str
    amenities: List[str]


class SchemaOrgRoom(BaseModel):
    context: str = Field(default="https://schema.org", alias="@context")
    type: str = Field(default="Room", alias="@type")
    name: str
    description: str
    bed: Dict[str, Any]
    occupancy: Dict[str, Any]
    priceSpecification: Dict[str, Any]
    amenities: List[str]


class SchemaOrgAvailability(BaseModel):
    context: str = Field(default="https://schema.org", alias="@context")
    type: str = Field(default="Offer", alias="@type")
    name: str
    price: float
    priceCurrency: str = "USD"
    availability: str
    availabilityStarts: Optional[date] = None
    availabilityEnds: Optional[date] = None
    eligibleRegion: Dict[str, Any]
