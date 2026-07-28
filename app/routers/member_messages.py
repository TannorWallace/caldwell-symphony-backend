from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from ..database import get_db
from ..models.models import MemberMessage as MemberMessageModel, User as UserModel
from ..schemas.member_message import (
    MemberMessage,
    MemberMessageCreate,
    MemberMessageUpdate,
)
from ..dependencies import get_current_member_user
from ..exceptions import NotFoundException, ForbiddenException

router = APIRouter(
    prefix="/api/v1/member-messages",
    tags=["Member Messages"]
)


def _serialize_message(message: MemberMessageModel, include_replies: bool = False) -> dict:
    """Safely convert a MemberMessage ORM object into a plain dict"""
    data = {
        "id": message.id,
        "content": message.content,
        "user_id": message.user_id,
        "parent_id": message.parent_id,
        "is_deleted": message.is_deleted,
        "created_at": message.created_at,
        "username": message.user.username if message.user else None,
        "full_name": message.user.full_name if message.user else None,
        "replies": [],
    }

    if include_replies and message.replies:
        data["replies"] = [
            _serialize_message(reply)
            for reply in message.replies
            if not reply.is_deleted
        ]

    return data


@router.get("/", response_model=List[MemberMessage])
async def list_member_messages(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_member_user),
):
    """
    Get all top-level member messages with their replies.
    Only accessible to members and admins.
    """
    result = await db.execute(
        select(MemberMessageModel)
        .options(
            selectinload(MemberMessageModel.user),
            selectinload(MemberMessageModel.replies).selectinload(MemberMessageModel.user),
        )
        .where(
            MemberMessageModel.parent_id == None,
            MemberMessageModel.is_deleted == False,
        )
        .order_by(MemberMessageModel.created_at.desc())
    )
    messages = result.scalars().all()

    return [_serialize_message(msg, include_replies=True) for msg in messages]


@router.post("/", response_model=MemberMessage, status_code=status.HTTP_201_CREATED)
async def create_member_message(
    message_in: MemberMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_member_user),
):
    """
    Create a new message or a reply.
    Members and admins only.
    """
    if message_in.parent_id is not None:
        parent_result = await db.execute(
            select(MemberMessageModel).where(
                MemberMessageModel.id == message_in.parent_id,
                MemberMessageModel.is_deleted == False,
            )
        )
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise NotFoundException("Parent message not found")

    db_message = MemberMessageModel(
        content=message_in.content.strip(),
        user_id=current_user.id,
        parent_id=message_in.parent_id,
    )

    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)

    # Re-fetch with user loaded
    result = await db.execute(
        select(MemberMessageModel)
        .options(selectinload(MemberMessageModel.user))
        .where(MemberMessageModel.id == db_message.id)
    )
    message = result.scalar_one()

    return _serialize_message(message)


@router.put("/{message_id}", response_model=MemberMessage)
async def update_member_message(
    message_id: int,
    message_in: MemberMessageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_member_user),
):
    """Update your own message"""
    result = await db.execute(
        select(MemberMessageModel)
        .options(selectinload(MemberMessageModel.user))
        .where(
            MemberMessageModel.id == message_id,
            MemberMessageModel.is_deleted == False,
        )
    )
    message = result.scalar_one_or_none()

    if not message:
        raise NotFoundException("Message not found")

    if message.user_id != current_user.id and not current_user.is_admin:
        raise ForbiddenException("You can only edit your own messages")

    message.content = message_in.content.strip()
    await db.commit()
    await db.refresh(message)

    return _serialize_message(message)


@router.delete("/{message_id}")
async def delete_member_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_member_user),
):
    """
    Soft-delete a message.
    - Members can delete their own messages
    - Admins can delete any message
    """
    result = await db.execute(
        select(MemberMessageModel).where(
            MemberMessageModel.id == message_id,
            MemberMessageModel.is_deleted == False,
        )
    )
    message = result.scalar_one_or_none()

    if not message:
        raise NotFoundException("Message not found")

    if message.user_id != current_user.id and not current_user.is_admin:
        raise ForbiddenException("You can only delete your own messages")

    message.is_deleted = True
    await db.commit()

    return {"message": "Message deleted successfully"}