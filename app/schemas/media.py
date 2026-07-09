from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class MediaBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    performance_id: Optional[int] = None   # NEW - allow linking to a performance


class MediaCreate(MediaBase):
    pass


class Media(MediaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    media_type: str
    bucket: str
    file_path: str
    public_url: str
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime
    user_id: int
    user_username: Optional[str] = None