import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.exceptions import NotFoundException, BadRequestException
from app.models.models import Spotlight, User
from app.schemas.spotlight import SpotlightOut, SpotlightUpdate
from app.supabase import supabase_storage
from app.uploads import read_gallery_file

router = APIRouter(prefix="/api/v1/spotlights", tags=["Spotlights"])

SPOTLIGHTS_BUCKET = "media"


def _object_path_from_public_url(url: str | None, bucket: str) -> str | None:
    if not url:
        return None
    marker = f"/object/public/{bucket}/"
    if marker not in url:
        return None
    return url.split(marker, 1)[1].split("?")[0]


async def _upload_poster(file: UploadFile) -> str:
    file_bytes, _media_type = await read_gallery_file(file)
    ext = Path(file.filename or "").suffix.lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise BadRequestException("Poster must be a JPG, PNG, or WEBP image")
    object_path = f"spotlights/{uuid.uuid4().hex}{ext}"
    await supabase_storage.upload_file(
        bucket=SPOTLIGHTS_BUCKET,
        file_path=object_path,
        file_bytes=file_bytes,
        content_type=file.content_type or "image/jpeg",
    )
    return supabase_storage.get_public_url(SPOTLIGHTS_BUCKET, object_path)


async def _delete_poster(image_url: str | None) -> None:
    object_path = _object_path_from_public_url(image_url, SPOTLIGHTS_BUCKET)
    if not object_path:
        return
    try:
        await supabase_storage.delete_file(SPOTLIGHTS_BUCKET, object_path)
    except Exception:
        pass


@router.get("/", response_model=list[SpotlightOut])
async def list_published_spotlights(
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
):
    result = await db.execute(
        select(Spotlight)
        .where(Spotlight.is_published.is_(True))
        .order_by(Spotlight.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/admin", response_model=list[SpotlightOut])
async def list_all_spotlights_admin(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(
        select(Spotlight).order_by(Spotlight.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=SpotlightOut, status_code=status.HTTP_201_CREATED)
async def create_spotlight(
    title: str = Form(...),
    body: str | None = Form(None),
    guidelines_url: str | None = Form(None),
    registration_url: str | None = Form(None),
    is_published: bool = Form(False),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    image_url = None
    if file is not None and file.filename:
        image_url = await _upload_poster(file)

    item = Spotlight(
        title=title.strip(),
        body=body.strip() if body else None,
        guidelines_url=guidelines_url.strip() if guidelines_url else None,
        registration_url=registration_url.strip() if registration_url else None,
        image_url=image_url,
        is_published=is_published,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/{spotlight_id}", response_model=SpotlightOut)
async def update_spotlight(
    spotlight_id: int,
    data: SpotlightUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(
        select(Spotlight).where(Spotlight.id == spotlight_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Spotlight not found")

    payload = data.model_dump(exclude_unset=True)
    if "title" in payload and payload["title"] is not None:
        payload["title"] = payload["title"].strip()
    if "body" in payload and payload["body"] is not None:
        payload["body"] = payload["body"].strip() or None
    if "guidelines_url" in payload and payload["guidelines_url"] is not None:
        payload["guidelines_url"] = payload["guidelines_url"].strip() or None
    if "registration_url" in payload and payload["registration_url"] is not None:
        payload["registration_url"] = payload["registration_url"].strip() or None

    for key, value in payload.items():
        setattr(item, key, value)

    await db.commit()
    await db.refresh(item)
    return item


@router.post("/{spotlight_id}/poster", response_model=SpotlightOut)
async def replace_spotlight_poster(
    spotlight_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(
        select(Spotlight).where(Spotlight.id == spotlight_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Spotlight not found")

    new_url = await _upload_poster(file)
    await _delete_poster(item.image_url)
    item.image_url = new_url
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{spotlight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_spotlight(
    spotlight_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(
        select(Spotlight).where(Spotlight.id == spotlight_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Spotlight not found")

    await _delete_poster(item.image_url)
    await db.delete(item)
    await db.commit()
    return None