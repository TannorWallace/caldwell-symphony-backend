from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from ..database import get_db
from ..models.models import Media as MediaModel, User as UserModel  # ← Use the model
from ..schemas.media import MediaCreate, Media     # ← Use the schema for response
from ..supabase import SupabaseStorage
from ..dependencies import get_current_active_user

router = APIRouter(
    prefix="/api/v1/media",
    tags=["Media"]
)

supabase_storage = SupabaseStorage()

# ==================== UPLOAD MEDIA ====================
@router.post("/", response_model=Media, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    title: str = None,
    description: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/webp", "video/mp4", "video/webm"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    media_type = "image" if file.content_type.startswith("image") else "video"

    # Generate unique file path
    file_ext = file.filename.split(".")[-1]
    file_path = f"{uuid.uuid4()}.{file_ext}"

    # Read file bytes
    file_bytes = await file.read()

    # Upload to Supabase Storage
    try:
        await supabase_storage.upload_file(
            bucket="media",
            file_path=file_path,
            file_bytes=file_bytes,
            content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    public_url = supabase_storage.get_public_url("media", file_path)

    # Save to database using the SQLAlchemy MODEL
    db_media = MediaModel(
        media_type=media_type,
        bucket="media",
        file_path=file_path,
        public_url=public_url,
        title=title,
        description=description,
        user_id=current_user.id   # ← This was missing
    )

    db.add(db_media)
    await db.commit()
    await db.refresh(db_media)

    return db_media


# ==================== GET ALL MEDIA (new endpoint) ====================
@router.get("/", response_model=List[Media])
async def get_all_media(
    db: AsyncSession = Depends(get_db)
):
    """Return all media, newest first"""
    result = await db.execute(
        select(MediaModel).order_by(MediaModel.created_at.desc())
    )
    return result.scalars().all()