from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, ForwardRef

# Forward reference for recursive replies
Comment = ForwardRef("Comment")


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    media_id: int
    parent_id: Optional[int] = None


class CommentUpdate(CommentBase):
    pass


class Comment(CommentBase):
    id: int
    user_id: int
    media_id: int
    parent_id: Optional[int] = None
    is_approved: bool
    is_deleted: bool
    created_at: datetime
    username: Optional[str] = None
    replies: List["Comment"] = Field(default_factory=list)

    class Config:
        from_attributes = True


# This is required for recursive Pydantic models
Comment.model_rebuild()