from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

from .media import Media   # We'll use this for nested responses later if needed


class PerformanceBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    cover_image_url: Optional[str] = None
    is_published: bool = True


class PerformanceCreate(PerformanceBase):
    pass


class PerformanceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    cover_image_url: Optional[str] = None
    is_published: Optional[bool] = None


class Performance(PerformanceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    # Optional: include media count or basic media list later
    # media: List[Media] = []