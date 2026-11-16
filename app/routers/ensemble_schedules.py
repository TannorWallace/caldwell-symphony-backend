from datetime import date, time

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies import get_current_admin_user, get_current_member_user
from ..exceptions import NotFoundException, BadRequestException
from ..models.models import RecurringSchedule, ScheduleException, User, UserEnsemble
from ..schemas.ensemble_schedule import (
    RecurringScheduleCreate,
    RecurringScheduleUpdate,
    RecurringScheduleOut,
    ScheduleExceptionCreate,
    ScheduleExceptionOut,
)

router = APIRouter(prefix="/api/v1/ensemble-schedules", tags=["Ensemble-Schedules"])


@router.get("/", response_model=list[RecurringScheduleOut])
async def list_schedules(
    group_slug: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_member_user),
):
    query = (
        select(RecurringSchedule)
        .options(selectinload(RecurringSchedule.exceptions))
        .order_by(RecurringSchedule.group_slug.asc(), RecurringSchedule.day_of_week.asc(), RecurringSchedule.start_time.asc())
    )

    slug = group_slug.strip() if group_slug else None

    if not current_user.is_admin:
        query = query.where(RecurringSchedule.is_published.is_(True))
        assigned = await db.execute(
            select(UserEnsemble.group_slug).where(UserEnsemble.user_id == current_user.id)
        )
        slugs = [row[0] for row in assigned.all()]
        if slug:
            if slug not in slugs:
                return []
            query = query.where(RecurringSchedule.group_slug == slug)
        else:
            if not slugs:
                return []
            query = query.where(RecurringSchedule.group_slug.in_(slugs))
    else:
        if slug:
            query = query.where(RecurringSchedule.group_slug == slug)

    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=RecurringScheduleOut, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    data: RecurringScheduleCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    if data.end_time <= data.start_time:
        raise BadRequestException("End time must be after start time")

    item = RecurringSchedule(
        group_slug=data.group_slug.strip(),
        title=data.title.strip(),
        notes=data.notes.strip() if data.notes else None,
        day_of_week=data.day_of_week,
        start_time=data.start_time,
        end_time=data.end_time,
        recurrence_start=data.recurrence_start,
        recurrence_end=data.recurrence_end,
        is_published=data.is_published,
        is_recurring=data.is_recurring,
        created_by=admin.id,
    )
    db.add(item)
    await db.commit()

    result = await db.execute(
        select(RecurringSchedule)
        .options(selectinload(RecurringSchedule.exceptions))
        .where(RecurringSchedule.id == item.id)
    )
    return result.scalar_one()


@router.put("/{item_id}", response_model=RecurringScheduleOut)
async def update_schedule(
    item_id: int,
    data: RecurringScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(
        select(RecurringSchedule)
        .options(selectinload(RecurringSchedule.exceptions))
        .where(RecurringSchedule.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Schedule not found")

    payload = data.model_dump(exclude_unset=True)
    if "title" in payload and payload["title"] is not None:
        payload["title"] = payload["title"].strip()
    if "notes" in payload and payload["notes"] is not None:
        payload["notes"] = payload["notes"].strip() or None
    if "group_slug" in payload and payload["group_slug"] is not None:
        payload["group_slug"] = payload["group_slug"].strip()

    start = payload.get("start_time", item.start_time)
    end = payload.get("end_time", item.end_time)
    if end and start and end <= start:
        raise BadRequestException("End time must be after start time")

    for key, value in payload.items():
        setattr(item, key, value)

    await db.commit()

    result = await db.execute(
        select(RecurringSchedule)
        .options(selectinload(RecurringSchedule.exceptions))
        .where(RecurringSchedule.id == item.id)
    )
    return result.scalar_one()


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(select(RecurringSchedule).where(RecurringSchedule.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Schedule not found")

    await db.delete(item)
    await db.commit()
    return None


@router.get("/{schedule_id}/exceptions", response_model=list[ScheduleExceptionOut])
async def list_exceptions(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_member_user),
):
    result = await db.execute(
        select(ScheduleException).where(ScheduleException.recurring_schedule_id == schedule_id)
    )
    return result.scalars().all()


@router.post("/exceptions", response_model=ScheduleExceptionOut, status_code=status.HTTP_201_CREATED)
async def create_exception(
    data: ScheduleExceptionCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    existing = await db.execute(
        select(ScheduleException).where(
            ScheduleException.recurring_schedule_id == data.recurring_schedule_id,
            ScheduleException.exception_date == data.exception_date,
        )
    )
    if existing.scalar_one_or_none():
        raise BadRequestException("Exception already exists for that date")

    item = ScheduleException(
        recurring_schedule_id=data.recurring_schedule_id,
        exception_date=data.exception_date,
        is_cancelled=data.is_cancelled,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/exceptions/{exception_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exception(
    exception_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(select(ScheduleException).where(ScheduleException.id == exception_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Exception not found")
    await db.delete(item)
    await db.commit()
    return None