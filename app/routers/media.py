from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import uuid

from ..database import get_db
from ..models.models import Media as MediaModel, User as UserModel
from ..schemas.media import MediaCreate, Media
from ..supabase import SupabaseStorage
from ..dependencies import get_current_active_user
from ..exceptions import BadRequestException

router = APIRouter(
    prefix="/api/v1/media",
    tags=["Media"]
)

supabase_storage = SupabaseStorage()


@router.post("/", response_model=Media, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    title: str = None,
    description: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp", "video/mp4", "video/webm"]:
        raise BadRequestException("Unsupported file type")

    media_type = "image" if file.content_type.startswith("image") else "video"

    file_ext = file.filename.split(".")[-1]
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
        user_id=current_user.id
    )

    db.add(db_media)
    await db.commit()
    await db.refresh(db_media)

    # Attach username for response
    db_media.user_username = current_user.username
    return db_media


@router.get("/", response_model=List[Media])
async def get_all_media(
    db: AsyncSession = Depends(get_db)
):
    """Return all media with uploader username, newest first"""
    result = await db.execute(
        select(MediaModel)
        .options(selectinload(MediaModel.user))
        .order_by(MediaModel.created_at.desc())
    )
    media_list = result.scalars().all()

    # Attach username from the loaded user relationship
    for media in media_list:
        if media.user:
            media.user_username = media.user.username

    return media_list