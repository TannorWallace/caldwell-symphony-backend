from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, Optional


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    media_id: int
    parent_id: Optional[int] = None


class CommentUpdate(CommentBase):
    pass


class Comment(CommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    media_id: int
    parent_id: Optional[int] = None
    is_approved: bool
    is_deleted: bool
    created_at: datetime
    username: Optional[str] = None
    replies: Optional[List["Comment"]] = Field(default_factory=list)


class CommentActivity(BaseModel):
    """Simplified comment for activity views (no nested replies)"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    user_id: int
    media_id: int
    parent_id: Optional[int] = None
    is_approved: bool
    is_deleted: bool
    created_at: datetime
    username: Optional[str] = None


# Rebuild for recursive model
Comment.model_rebuild()