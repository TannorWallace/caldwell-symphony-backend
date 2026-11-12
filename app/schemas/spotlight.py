from datetime import datetime
from pydantic import BaseModel


class SpotlightCreate(BaseModel):
    title: str
    body: str | None = None
    guidelines_url: str | None = None
    registration_url: str | None = None
    is_published: bool = False


class SpotlightUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    guidelines_url: str | None = None
    registration_url: str | None = None
    is_published: bool | None = None
    image_url: str | None = None


class SpotlightOut(BaseModel):
    id: int
    title: str
    body: str | None
    guidelines_url: str | None
    registration_url: str | None
    image_url: str | None
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True