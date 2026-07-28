from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, Optional


class MemberMessageBase(BaseModel):
    content: str


class MemberMessageCreate(MemberMessageBase):
    parent_id: Optional[int] = None


class MemberMessageUpdate(BaseModel):
    content: str


class MemberMessage(MemberMessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    parent_id: Optional[int] = None
    is_deleted: bool
    created_at: datetime
    username: Optional[str] = None
    full_name: Optional[str] = None
    replies: Optional[List["MemberMessage"]] = Field(default_factory=list)


# Rebuild for recursive model
MemberMessage.model_rebuild()