from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..dependencies import get_current_active_user
from ..models.models import Comment as CommentModel, User as UserModel
from ..schemas.comment import Comment, CommentCreate, CommentUpdate
from ..schemas.user import PaginatedResponse   # ← Make sure this exists

router = APIRouter(prefix="/api/v1/comments", tags=["comments"])


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
            raise HTTPException(status_code=400, detail="Invalid parent comment or media mismatch")

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
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")
    if comment.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot edit a deleted comment")

    comment.content = comment_in.content
    await db.commit()
    await db.refresh(comment)

    if comment.user:
        comment.username = comment.user.username
    return comment


# ==================== DELETE OWN COMMENT + ALL REPLIES ====================
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
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")
    if comment.is_deleted:
        raise HTTPException(status_code=400, detail="Comment is already deleted")

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


# ==================== GET COMMENTS FOR MEDIA (WITH PAGINATION) ====================
@router.get("/media/{media_id}", response_model=PaginatedResponse)
async def get_comments_for_media(
    media_id: int,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    db: AsyncSession = Depends(get_db),
):
    """Paginated flat list of comments for a media item.
    Frontend uses parent_id to build the threaded tree."""
    
    # Total count for pagination
    count_result = await db.execute(
        select(CommentModel)
        .where(
            CommentModel.media_id == media_id,
            CommentModel.is_approved == True,
            CommentModel.is_deleted == False,
        )
    )
    total = len(count_result.scalars().all())

    # Paginated comments
    result = await db.execute(
        select(CommentModel)
        .options(selectinload(CommentModel.user))
        .where(
            CommentModel.media_id == media_id,
            CommentModel.is_approved == True,
            CommentModel.is_deleted == False,
        )
        .order_by(CommentModel.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    comments = result.scalars().all()

    for comment in comments:
        if comment.user:
            comment.username = comment.user.username

    return {
        "items": comments,
        "total": total,
        "skip": skip,
        "limit": limit
    }