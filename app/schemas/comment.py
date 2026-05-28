from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    """Used only when creating a new comment/reply"""
    media_id: int
    parent_id: Optional[int] = None

class CommentUpdate(CommentBase):
    """Used only when updating an existing comment"""
    # Only content is allowed to be updated
    pass

class Comment(CommentBase):
    id: int
    user_id: int
    media_id: int
    parent_id: Optional[int] = None
    is_approved: bool
    is_deleted: bool
    created_at: datetime
    username: Optional[str] = None          # ← We will manually set this


    #muckin my day up
    # replies: List["Comment"] = Field(default_factory=list)

    class Config:
        from_attributes = True

# Required for recursive nested model
Comment.model_rebuild()