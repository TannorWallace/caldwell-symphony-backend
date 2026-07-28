from typing import List
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.models import Performance as PerformanceModel, Media
from ..schemas.performance import Performance, PerformanceDetail
from ..exceptions import NotFoundException

router = APIRouter(
    prefix="/api/v1/performances",
    tags=["Performances"]
)


@router.get("/", response_model=List[Performance])
async def list_performances(
    db: AsyncSession = Depends(get_db)
):
    """Public gallery: published + has at least one media item."""
    has_media = exists().where(
        Media.performance_id == PerformanceModel.id
    )

    result = await db.execute(
        select(PerformanceModel)
        .options(selectinload(PerformanceModel.cover_media))
        .where(
            PerformanceModel.is_published == True,
            has_media,
        )
        .order_by(PerformanceModel.created_at.desc())
    )
    performances = result.scalars().all()

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
    """Public: only published performances"""
    result = await db.execute(
        select(PerformanceModel)
        .options(
            selectinload(PerformanceModel.media).selectinload(Media.user),
            selectinload(PerformanceModel.cover_media)
        )
        .where(
            PerformanceModel.id == performance_id,
            PerformanceModel.is_published == True,
        )
    )
    performance = result.scalar_one_or_none()
    if not performance:
        raise NotFoundException("Performance not found")

    for media in performance.media:
        if media.user:
            media.user_username = media.user.username

    if performance.cover_media:
        performance.cover_image_url = performance.cover_media.public_url
    else:
        performance.cover_image_url = None

    return performance