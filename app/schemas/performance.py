from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

from .media import Media


class PerformanceBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_published: bool = True


class PerformanceCreate(PerformanceBase):
    pass


class PerformanceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cover_media_id: Optional[int] = None
    is_published: Optional[bool] = None


class Performance(PerformanceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cover_media_id: Optional[int] = None
    cover_image_url: Optional[str] = None   # convenient field for frontend
    created_by: int
    created_at: datetime
    updated_at: datetime


class PerformanceDetail(Performance):
    media: List[Media] = []