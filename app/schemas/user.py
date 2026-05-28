from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# Import other schemas we need
from .comment import Comment
from .media import Media


# ==================== BASIC USER SCHEMAS ====================
class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserDelete(BaseModel):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ==================== USER ACTIVITY ====================
class UserActivity(BaseModel):
    total_comments: int
    total_media: int
    recent_comments: List[Comment]
    my_media: List[Media]

    class Config:
        from_attributes = True


# ==================== PAGINATED RESPONSE (for comments) ====================
class PaginatedResponse(BaseModel):
    items: List[Comment]
    total: int
    skip: int
    limit: int

    class Config:
        from_attributes = True