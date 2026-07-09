from fastapi import APIRouter, Depends, status, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List

from ..database import get_db
from ..dependencies import get_current_active_user
from ..models.models import Comment as CommentModel, User as UserModel
from ..schemas.comment import Comment, CommentCreate, CommentUpdate
from ..exceptions import NotFoundException, ForbiddenException, BadRequestException

router = APIRouter(prefix="/api/v1/comments", tags=["comments"])


# ==================== GET COMMENTS FOR MEDIA ====================
@router.get("/media/{media_id}", response_model=List[Comment])
async def get_comments_for_media(
    media_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all approved comments with nested replies."""
    result = await db.execute(
        select(CommentModel)
        .options(selectinload(CommentModel.user))
        .where(
            CommentModel.media_id == media_id,
            CommentModel.is_approved == True,
            CommentModel.is_deleted == False,
        )
        .order_by(CommentModel.created_at.asc())
    )
    flat_comments = result.scalars().all()

    # Attach username
    for comment in flat_comments:
        if comment.user:
            comment.username = comment.user.username

    def build_nested_tree(comments: list) -> list:
        comment_map = {c.id: c for c in comments}

        for comment in comments:
            comment.__dict__['replies'] = []

        roots = []
        for comment in comments:
            if comment.parent_id is None:
                roots.append(comment)
            else:
                parent = comment_map.get(comment.parent_id)
                if parent:
                    if not parent.__dict__.get('replies'):
                        parent.__dict__['replies'] = []
                    parent.__dict__['replies'].append(comment)
        return roots

    return build_nested_tree(flat_comments)


# ==================== CREATE COMMENT / REPLY ====================
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

    # Reload with user relationship
    result = await db.execute(
        select(CommentModel)
        .options(selectinload(CommentModel.user))
        .where(CommentModel.id == db_comment.id)
    )
    comment = result.scalar_one_or_none()

    if comment:
        # Safely initialize replies to prevent lazy-loading during serialization
        comment.__dict__['replies'] = []
        
        if comment.user:
            comment.username = comment.user.username

    return comment


# ==================== UPDATE OWN COMMENT ====================
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

    # === FIX: Prevent MissingGreenlet error on replies during serialization ===
    comment.__dict__['replies'] = []

    if comment.user:
        comment.username = comment.user.username

    return comment


# ==================== DELETE OWN COMMENT (with cascade to replies) ====================
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