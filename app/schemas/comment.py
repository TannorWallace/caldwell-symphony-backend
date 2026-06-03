from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    """Used only when creating a new comment/reply"""
    media_id: int
    parent_id: Optional[int] = None


class CommentUpdate(CommentBase):
    """Used only when updating an existing comment"""
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


# Required for recursive nested model (if you ever re-enable replies)
Comment.model_rebuild()