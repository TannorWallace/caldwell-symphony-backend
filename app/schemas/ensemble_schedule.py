from datetime import date, time, datetime
from pydantic import BaseModel, Field


class ScheduleExceptionOut(BaseModel):
    id: int
    recurring_schedule_id: int
    exception_date: date
    is_cancelled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RecurringScheduleCreate(BaseModel):
    group_slug: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    notes: str | None = None
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday ... 6=Sunday
    start_time: time
    end_time: time
    recurrence_start: date
    recurrence_end: date | None = None
    is_published: bool = True
    is_recurring: bool = False


class RecurringScheduleUpdate(BaseModel):
    group_slug: str | None = Field(None, min_length=1, max_length=100)  # ← add
    title: str | None = Field(None, min_length=1, max_length=200)
    notes: str | None = None
    day_of_week: int | None = Field(None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    recurrence_start: date | None = None
    recurrence_end: date | None = None
    is_published: bool | None = None
    is_recurring: bool | None = None


class RecurringScheduleOut(BaseModel):
    id: int
    group_slug: str
    title: str
    notes: str | None
    day_of_week: int
    start_time: time
    end_time: time
    recurrence_start: date
    recurrence_end: date | None
    is_published: bool
    is_recurring: bool
    created_by: int | None
    created_at: datetime
    updated_at: datetime
    exceptions: list[ScheduleExceptionOut] = []

    class Config:
        from_attributes = True


class ScheduleExceptionCreate(BaseModel):
    recurring_schedule_id: int
    exception_date: date
    is_cancelled: bool = True