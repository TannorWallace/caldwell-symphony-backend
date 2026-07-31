from datetime import datetime
from pydantic import BaseModel, Field


class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str | None = None
    image_url: str | None = None
    is_published: bool = False


class AnnouncementUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    body: str | None = None
    image_url: str | None = None
    is_published: bool | None = None


class AnnouncementOut(BaseModel):
    id: int
    title: str
    body: str | None
    image_url: str | None
    is_published: bool
    created_by: int | None
    created_at: datetime

    class Config:
        from_attributes = True