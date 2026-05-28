from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MediaBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class MediaCreate(MediaBase):
    pass

class Media(MediaBase):
    id: Optional[int] = None
    media_type: str
    bucket: str
    file_path: str
    public_url: str
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    created_at: Optional[datetime] = None
    user_id: int                     # ← Added so activity endpoint works

    class Config:
        from_attributes = True