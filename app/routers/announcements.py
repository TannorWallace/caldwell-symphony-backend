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
from app.uploads import read_flyer_file

router = APIRouter(prefix="/api/v1/announcements", tags=["announcements"])

ANNOUNCEMENTS_BUCKET = "media"


def _object_path_from_public_url(url: str | None, bucket: str) -> str | None:
    if not url:
        return None
    marker = f"/object/public/{bucket}/"
    if marker not in url:
        return None
    return url.split(marker, 1)[1].split("?")[0]


@router.get("/admin", response_model=list[AnnouncementOut])
async def list_all_announcements_admin(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(
        select(Announcement).order_by(Announcement.created_at.desc())
    )
    return result.scalars().all()


@router.get("/", response_model=list[AnnouncementOut])
async def list_published_announcements(
    group_slug: str | None = None,
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
):
    query = (
        select(Announcement)
        .where(Announcement.is_published.is_(True))
        .order_by(Announcement.created_at.desc())
        .limit(limit)
    )

    if group_slug:
        # Ensemble portal: only this group's announcements
        query = query.where(Announcement.group_slug == group_slug)
    else:
        # Homepage: only announcements with no group_slug
        query = query.where(Announcement.group_slug.is_(None))

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    title: str = Form(...),
    body: str | None = Form(None),
    is_published: bool = Form(False),
    group_slug: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    image_url = None

    if file is not None and file.filename:
        file_bytes = await read_flyer_file(file)
        ext = Path(file.filename).suffix.lower() or ".jpg"
        object_path = f"announcements/{uuid.uuid4().hex}{ext}"
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
        group_slug=group_slug.strip() if group_slug else None,
        created_by=admin.id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/{announcement_id}", response_model=AnnouncementOut)
async def update_announcement(
    announcement_id: int,
    data: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")

    if data.title is not None:
        item.title = data.title.strip()
    if data.body is not None:
        item.body = data.body.strip() if data.body else None
    if data.is_published is not None:
        item.is_published = data.is_published
    if data.group_slug is not None:
        item.group_slug = data.group_slug.strip() if data.group_slug else None

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