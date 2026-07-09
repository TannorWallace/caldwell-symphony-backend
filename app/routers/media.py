from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, status, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import uuid

from ..database import get_db
from ..models.models import Media as MediaModel, User as UserModel, Performance as PerformanceModel
from ..schemas.media import MediaCreate, Media
from ..supabase import SupabaseStorage
from ..dependencies import get_current_active_user
from ..exceptions import BadRequestException, NotFoundException

router = APIRouter(
    prefix="/api/v1/media",
    tags=["Media"]
)

supabase_storage = SupabaseStorage()


@router.post("/", response_model=Media, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    performance_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "video/mp4", "video/webm"]
    if file.content_type not in allowed_types:
        raise BadRequestException("Unsupported file type. Allowed: JPEG, PNG, WEBP, MP4, WEBM")

    # Validate performance exists if performance_id is provided
    if performance_id is not None:
        result = await db.execute(
            select(PerformanceModel).where(PerformanceModel.id == performance_id)
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Performance not found")

    media_type = "image" if file.content_type.startswith("image") else "video"

    file_ext = file.filename.split(".")[-1] if file.filename else "bin"
    file_path = f"{uuid.uuid4()}.{file_ext}"

    file_bytes = await file.read()

    try:
        await supabase_storage.upload_file(
            bucket="media",
            file_path=file_path,
            file_bytes=file_bytes,
            content_type=file.content_type
        )
    except Exception as e:
        raise BadRequestException(f"Upload failed: {str(e)}")

    public_url = supabase_storage.get_public_url("media", file_path)

    db_media = MediaModel(
        media_type=media_type,
        bucket="media",
        file_path=file_path,
        public_url=public_url,
        title=title,
        description=description,
        user_id=current_user.id,
        performance_id=performance_id
    )

    db.add(db_media)
    await db.commit()
    await db.refresh(db_media)

    # Attach username for the response (using the current user from auth)
    db_media.user_username = current_user.username
    return db_media


@router.get("/", response_model=List[Media])
async def get_all_media(
    performance_id: Optional[int] = Query(None, description="Filter by performance ID"),
    db: AsyncSession = Depends(get_db)
):
    """Return all media items. Optionally filter by performance_id."""
    query = (
        select(MediaModel)
        .options(selectinload(MediaModel.user))
        .order_by(MediaModel.created_at.desc())
    )

    if performance_id is not None:
        query = query.where(MediaModel.performance_id == performance_id)

    result = await db.execute(query)
    media_list = result.scalars().all()

    # Attach username from the loaded user relationship
    for media in media_list:
        if media.user:
            media.user_username = media.user.username

    return media_list