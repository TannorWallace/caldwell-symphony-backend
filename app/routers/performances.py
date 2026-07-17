from typing import List
from fastapi import APIRouter, Depends, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.models import Performance as PerformanceModel, User as UserModel, Media
from ..schemas.performance import Performance, PerformanceCreate, PerformanceDetail, PerformanceUpdate
from ..dependencies import get_current_admin_user
from ..exceptions import NotFoundException

router = APIRouter(
    prefix="/api/v1/performances",
    tags=["Performances"]
)

# ==================== PUBLIC ENDPOINTS ====================

@router.get("/", response_model=List[Performance])
async def list_performances(
    db: AsyncSession = Depends(get_db)
):
    """Get all published performances (newest first) with cover image"""
    result = await db.execute(
        select(PerformanceModel)
        .options(selectinload(PerformanceModel.cover_media))
        .where(PerformanceModel.is_published == True)
        .order_by(PerformanceModel.created_at.desc())
    )
    performances = result.scalars().all()

    # Attach a convenient cover_image_url for the frontend
    for perf in performances:
        if perf.cover_media:
            perf.cover_image_url = perf.cover_media.public_url
        else:
            perf.cover_image_url = None

    return performances


@router.get("/{performance_id}", response_model=PerformanceDetail)
async def get_performance(
    performance_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db)
):
    """Get a single performance by ID (with its media and uploader info)"""
    result = await db.execute(
        select(PerformanceModel)
        .options(
            selectinload(PerformanceModel.media).selectinload(Media.user),
            selectinload(PerformanceModel.cover_media)
        )
        .where(PerformanceModel.id == performance_id)
    )
    performance = result.scalar_one_or_none()
    if not performance:
        raise NotFoundException("Performance not found")

    # Populate user_username on each media item
    for media in performance.media:
        if media.user:
            media.user_username = media.user.username

    # Attach cover image url if it exists
    if performance.cover_media:
        performance.cover_image_url = performance.cover_media.public_url
    else:
        performance.cover_image_url = None

    return performance


# ==================== ADMIN ENDPOINTS ====================
# (These are not currently used because we put the admin endpoints in admin.py)
# Keeping them here for reference / future use

admin_router = APIRouter(
    prefix="/api/v1/admin/performances",
    tags=["Admin - Performances"]
)


@admin_router.post("/", response_model=Performance, status_code=status.HTTP_201_CREATED)
async def create_performance(
    performance_in: PerformanceCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    db_performance = PerformanceModel(
        **performance_in.model_dump(),
        created_by=current_admin.id
    )
    db.add(db_performance)
    await db.commit()
    await db.refresh(db_performance)
    return db_performance


@admin_router.put("/{performance_id}", response_model=Performance)
async def update_performance(
    performance_id: int,
    performance_in: PerformanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    result = await db.execute(select(PerformanceModel).where(PerformanceModel.id == performance_id))
    performance = result.scalar_one_or_none()
    if not performance:
        raise NotFoundException("Performance not found")

    update_data = performance_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(performance, field, value)

    await db.commit()
    await db.refresh(performance)
    return performance


@admin_router.delete("/{performance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_performance(
    performance_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    result = await db.execute(select(PerformanceModel).where(PerformanceModel.id == performance_id))
    performance = result.scalar_one_or_none()
    if not performance:
        raise NotFoundException("Performance not found")

    await db.delete(performance)
    await db.commit()
    return None