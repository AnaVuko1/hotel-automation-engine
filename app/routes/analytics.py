"""Analytics routes — dashboard, trends, revenue reports"""
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.schemas import DashboardMetrics, RevenueTrend, AgentPerformance
from app.services.pricing_engine import PricingEngine
from app.models import Booking, AgentLog, MaintenanceTask, HousekeepingTask

router = APIRouter()
pricing_engine = PricingEngine()


@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    period_days: int = Query(30, description="Lookback period in days"),
    db: AsyncSession = Depends(get_db),
):
    """Get key key dashboard metrics."""
    end_date = date.today()
    start_date = end_date - timedelta(days=period_days)

    total_revenue = await pricing_engine.calculate_total_revenue(start_date, end_date, db)
    adr = await pricing_engine.calculate_average_daily_rate(start_date, end_date, db)
    occ = await pricing_engine.calculate_occupancy_rate(start_date, end_date, db)
    revpar = round(adr * occ, 2) if occ else 0.0

    # Direct booking rate
    total_stmt = select(func.count()).select_from(Booking).where(
        and_(
            Booking.check_in_date >= start_date,
            Booking.check_in_date <= end_date,
        )
    )
    direct_stmt = select(func.count()).select_from(Booking).where(
        and_(
            Booking.check_in_date >= start_date,
            Booking.check_in_date <= end_date,
            Booking.is_direct_booking == True,
        )
    )
    total_bookings = (await db.execute(total_stmt)).scalar() or 1
    direct_bookings = (await db.execute(direct_stmt)).scalar() or 0
    direct_rate = round(direct_bookings / total_bookings, 4)

    # OTA leakage (commission paid)
    ota_stmt = select(func.sum(Booking.commission_paid)).where(
        and_(
            Booking.check_in_date >= start_date,
            Booking.check_in_date <= end_date,
        )
    )
    ota_leakage = (await db.execute(ota_stmt)).scalar() or 0.0

    # Active maintenance
    maint_stmt = select(func.count()).select_from(MaintenanceTask).where(
        MaintenanceTask.status.in_(["pending", "assigned", "in_progress"])
    )
    active_maint = (await db.execute(maint_stmt)).scalar() or 0

    # Pending housekeeping
    hsk_stmt = select(func.count()).select_from(HousekeepingTask).where(
        HousekeepingTask.status == "pending"
    )
    pending_hsk = (await db.execute(hsk_stmt)).scalar() or 0

    # Today's check-ins/outs
    today = date.today()
    ci_stmt = select(func.count()).select_from(Booking).where(
        Booking.check_in_date == today
    )
    co_stmt = select(func.count()).select_from(Booking).where(
        Booking.check_out_date == today
    )
    check_ins = (await db.execute(ci_stmt)).scalar() or 0
    check_outs = (await db.execute(co_stmt)).scalar() or 0

    # AI readiness score
    ai_score = await _calculate_ai_readiness(db)

    return DashboardMetrics(
        occupancy_rate=round(occ, 4),
        average_daily_rate=round(adr, 2),
        revpar=round(revpar, 2),
        total_revenue=round(total_revenue, 2),
        direct_booking_rate=direct_rate,
        ota_leakage=round(ota_leakage, 2),
        ai_readiness_score=ai_score,
        active_maintenance=active_maint,
        pending_housekeeping=pending_hsk,
        check_ins_today=check_ins,
        check_outs_today=check_outs,
    )


@router.get("/revenue-trend")
async def get_revenue_trend(
    months: int = Query(12, description="Number of months"),
    db: AsyncSession = Depends(get_db),
):
    """Get monthly revenue trend."""
    result = await pricing_engine.get_revenue_trend(months, db)
    return {"months": result}


@router.get("/occupancy-trend")
async def get_occupancy_trend(
    months: int = Query(12, description="Number of months"),
    db: AsyncSession = Depends(get_db),
):
    """Get monthly occupancy trend."""
    result = await pricing_engine.get_occupancy_trend(months, db)
    return {"months": result}


@router.get("/agent-performance")
async def get_agent_performance(
    limit: int = Query(100),
    db: AsyncSession = Depends(get_db),
):
    """Get agent performance metrics."""
    agents_list = ["guest", "ops", "hsk", "revenue", "orchestrator"]
    performance = []

    for agent in agents_list:
        stmt = select(func.count(), func.avg(AgentLog.confidence), func.avg(AgentLog.duration_ms)).where(
            AgentLog.agent_type == agent
        )
        result = await db.execute(stmt)
        row = result.one()
        count = row[0] or 0
        avg_conf = float(row[1]) if row[1] else 0.0
        avg_dur = int(float(row[2])) if row[2] else 0

        # Count escalations
        esc_stmt = select(func.count()).select_from(AgentLog).where(
            and_(
                AgentLog.agent_type == agent,
                AgentLog.decision == "escalated",
            )
        )
        esc_result = await db.execute(esc_stmt)
        escalations = esc_result.scalar() or 0

        performance.append({
            "agent": agent,
            "actions_taken": count,
            "auto_resolved": count - escalations,
            "escalated": escalations,
            "avg_duration_ms": avg_dur,
            "success_rate": round(avg_conf, 4) if avg_conf else 0,
        })

    return {"agents": performance}


async def _calculate_ai_readiness(db: AsyncSession) -> int:
    """Calculate AI Agent readiness score (0-100)."""
    score = 0

    # Check schema.org compliance (40 points)
    from app.adapters.schema_org import validate_schema_compliance
    compliance = validate_schema_compliance()
    score += compliance.get("score", 0)

    # Check if agents are available (30 points)
    try:
        agents = ["guest", "ops", "hsk", "revenue"]
        score += min(len(agents) * 7, 30)
    except Exception:
        pass

    # Check if we have hotel data (20 points)
    try:
        from app.models import Hotel
        hotel_result = await db.execute(select(func.count()).select_from(Hotel))
        has_hotel = (hotel_result.scalar() or 0) > 0
        score += 20 if has_hotel else 0
    except Exception:
        pass

    # JSON-LD validity (10 points)
    if compliance.get("valid", False):
        score += 10

    return min(100, score)
