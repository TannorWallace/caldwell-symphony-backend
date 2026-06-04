from fastapi import APIRouter, Depends, status, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies import get_current_active_user
from ..models.models import Comment as CommentModel, User as UserModel
from ..schemas.comment import Comment, CommentCreate, CommentUpdate
from ..schemas.user import PaginatedResponse
from ..exceptions import NotFoundException, ForbiddenException, BadRequestException

router = APIRouter(prefix="/api/v1/comments", tags=["comments"])


@router.post("/", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_in: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    if comment_in.parent_id is not None:
        parent_result = await db.execute(
            select(CommentModel).where(CommentModel.id == comment_in.parent_id)
        )
        parent = parent_result.scalar_one_or_none()
        if not parent or parent.media_id != comment_in.media_id:
            raise BadRequestException("Invalid parent comment or media mismatch")

    db_comment = CommentModel(
        content=comment_in.content,
        user_id=current_user.id,
        media_id=comment_in.media_id,
        parent_id=comment_in.parent_id,
        is_approved=True,
        is_deleted=False,
    )

    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)

    result = await db.execute(
        select(CommentModel)
        .options(selectinload(CommentModel.user))
        .where(CommentModel.id == db_comment.id)
    )
    comment = result.scalar_one_or_none()
    if comment and comment.user:
        comment.username = comment.user.username
    return comment


@router.put("/{comment_id}", response_model=Comment)
async def update_own_comment(
    comment_id: int,
    comment_in: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    result = await db.execute(
        select(CommentModel)
        .options(selectinload(CommentModel.user))
        .where(CommentModel.id == comment_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise NotFoundException("Comment not found")

    if comment.user_id != current_user.id:
        await db.rollback()
        raise ForbiddenException("You can only edit your own comments")

    if comment.is_deleted:
        raise BadRequestException("Cannot edit a deleted comment")

    comment.content = comment_in.content
    await db.commit()
    await db.refresh(comment)

    if comment.user:
        comment.username = comment.user.username
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_own_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """Soft-delete this comment AND all its replies (recursive)"""
    result = await db.execute(select(CommentModel).where(CommentModel.id == comment_id))
    comment = result.scalar_one_or_none()

    if not comment:
        raise NotFoundException("Comment not found")

    if comment.user_id != current_user.id:
        await db.rollback()
        raise ForbiddenException("You can only delete your own comments")

    if comment.is_deleted:
        raise BadRequestException("Comment is already deleted")

    ids_to_delete = [comment_id]
    to_check = [comment_id]

    while to_check:
        current = to_check.pop()
        child_result = await db.execute(
            select(CommentModel.id).where(CommentModel.parent_id == current)
        )
        children = child_result.scalars().all()
        for child_id in children:
            ids_to_delete.append(child_id)
            to_check.append(child_id)

    await db.execute(
        update(CommentModel)
        .where(CommentModel.id.in_(ids_to_delete))
        .values(is_deleted=True)
    )
    await db.commit()