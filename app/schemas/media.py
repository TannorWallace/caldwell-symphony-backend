from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class MediaBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class MediaCreate(MediaBase):
    pass


class Media(MediaBase):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    media_type: str
    bucket: str
    file_path: str
    public_url: str
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    created_at: Optional[datetime] = None
    user_id: int