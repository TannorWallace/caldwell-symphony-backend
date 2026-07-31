import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models.models import Announcement, User
from app.schemas.announcement import AnnouncementOut, AnnouncementUpdate
from app.supabase import supabase_storage

router = APIRouter(prefix="/api/v1/announcements", tags=["announcements"])

# Use the same public bucket as your media uploads if different
ANNOUNCEMENTS_BUCKET = "media"


@router.get("/", response_model=list[AnnouncementOut])
async def list_published_announcements(
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
):
    result = await db.execute(
        select(Announcement)
        .where(Announcement.is_published.is_(True))
        .order_by(Announcement.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/admin", response_model=list[AnnouncementOut])
async def list_all_announcements(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(
        select(Announcement).order_by(Announcement.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    title: str = Form(...),
    body: str | None = Form(None),
    is_published: bool = Form(False),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    image_url = None

    if file is not None and file.filename:
        ext = Path(file.filename).suffix.lower() or ".jpg"
        object_path = f"announcements/{uuid.uuid4().hex}{ext}"
        file_bytes = await file.read()
        content_type = file.content_type or "application/octet-stream"

        await supabase_storage.upload_file(
            bucket=ANNOUNCEMENTS_BUCKET,
            file_path=object_path,
            file_bytes=file_bytes,
            content_type=content_type,
        )
        image_url = supabase_storage.get_public_url(
            ANNOUNCEMENTS_BUCKET,
            object_path,
        )

    item = Announcement(
        title=title.strip(),
        body=body.strip() if body else None,
        image_url=image_url,
        is_published=is_published,
        created_by=admin.id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/{announcement_id}", response_model=AnnouncementOut)
async def update_announcement(
    announcement_id: int,
    payload: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")

    data = payload.model_dump(exclude_unset=True)
    if "title" in data and data["title"] is not None:
        data["title"] = data["title"].strip()
    if "body" in data and data["body"] is not None:
        data["body"] = data["body"].strip() or None

    for key, value in data.items():
        setattr(item, key, value)

    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")

    await db.delete(item)
    await db.commit()
    return None