from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, List

from .comment import Comment, CommentActivity
from .media import Media


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):                     # ← NEW
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime


class UserDelete(BaseModel):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserActivity(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_comments: int
    total_media: int
    recent_comments: List[CommentActivity]     # ← changed from Comment
    my_media: List[Media]


class PaginatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[Comment]
    total: int
    skip: int
    limit: int