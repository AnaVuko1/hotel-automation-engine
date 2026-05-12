"""Operations routes — maintenance and housekeeping CRUD"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.schemas import (
    MaintenanceTaskCreate, MaintenanceTaskUpdate, MaintenanceTaskResponse,
    HousekeepingTaskCreate, HousekeepingTaskUpdate, HousekeepingTaskResponse,
)
from app.models import MaintenanceTask, HousekeepingTask, TaskStatus

router = APIRouter()


# ─── Maintenance ─────────────────────────────────────────────────────────────

@router.post("/maintenance", response_model=MaintenanceTaskResponse)
async def create_maintenance_task(
    task: MaintenanceTaskCreate,
    db: AsyncSession = Depends(get_db),
):
    db_task = MaintenanceTask(**task.model_dump())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


@router.get("/maintenance", response_model=List[MaintenanceTaskResponse])
async def list_maintenance_tasks(
    hotel_id: int = Query(1),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    conditions = [MaintenanceTask.hotel_id == hotel_id]
    if status:
        conditions.append(MaintenanceTask.status == status)
    if priority:
        conditions.append(MaintenanceTask.priority == priority)

    stmt = select(MaintenanceTask).where(and_(*conditions)).order_by(
        MaintenanceTask.created_at.desc()
    ).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/maintenance/{task_id}", response_model=MaintenanceTaskResponse)
async def update_maintenance_task(
    task_id: int,
    update: MaintenanceTaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MaintenanceTask).where(MaintenanceTask.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Maintenance task not found")

    for key, val in update.model_dump(exclude_unset=True).items():
        setattr(task, key, val)

    if update.status == "completed":
        task.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(task)
    return task


@router.get("/maintenance/summary")
async def maintenance_summary(
    hotel_id: int = Query(1),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func
    counts = {}
    for status in TaskStatus:
        stmt = select(func.count()).select_from(MaintenanceTask).where(
            and_(
                MaintenanceTask.hotel_id == hotel_id,
                MaintenanceTask.status == status.value,
            )
        )
        result = await db.execute(stmt)
        counts[status.value] = result.scalar() or 0

    return {"hotel_id": hotel_id, "total": sum(counts.values()), "by_status": counts}


# ─── Housekeeping ───────────────────────────────────────────────────────────

@router.post("/housekeeping", response_model=HousekeepingTaskResponse)
async def create_housekeeping_task(
    task: HousekeepingTaskCreate,
    db: AsyncSession = Depends(get_db),
):
    db_task = HousekeepingTask(**task.model_dump())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


@router.get("/housekeeping", response_model=List[HousekeepingTaskResponse])
async def list_housekeeping_tasks(
    hotel_id: int = Query(1),
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    conditions = [HousekeepingTask.hotel_id == hotel_id]
    if status:
        conditions.append(HousekeepingTask.status == status)
    if task_type:
        conditions.append(HousekeepingTask.task_type == task_type)

    stmt = select(HousekeepingTask).where(and_(*conditions)).order_by(
        HousekeepingTask.created_at.desc()
    ).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/housekeeping/{task_id}", response_model=HousekeepingTaskResponse)
async def update_housekeeping_task(
    task_id: int,
    update: HousekeepingTaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(HousekeepingTask).where(HousekeepingTask.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Housekeeping task not found")

    for key, val in update.model_dump(exclude_unset=True).items():
        setattr(task, key, val)

    if update.status == "completed" and not task.completed_at:
        task.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(task)
    return task


@router.get("/housekeeping/summary")
async def housekeeping_summary(
    hotel_id: int = Query(1),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func
    counts = {}
    for status in TaskStatus:
        stmt = select(func.count()).select_from(HousekeepingTask).where(
            and_(
                HousekeepingTask.hotel_id == hotel_id,
                HousekeepingTask.status == status.value,
            )
        )
        result = await db.execute(stmt)
        counts[status.value] = result.scalar() or 0

    return {"hotel_id": hotel_id, "total": sum(counts.values()), "by_status": counts}
