from datetime import datetime
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    location: str | None = None
    price: str | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    group_slug: str = Field(..., min_length=1, max_length=100)
    is_published: bool = False


class EventUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    location: str | None = None
    price: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    group_slug: str | None = Field(None, min_length=1, max_length=100)
    is_published: bool | None = None


class EventOut(BaseModel):
    id: int
    title: str
    description: str | None
    location: str | None
    price: str | None
    starts_at: datetime
    ends_at: datetime | None
    group_slug: str
    image_url: str | None
    is_published: bool
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True