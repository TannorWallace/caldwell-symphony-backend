import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_admin_user
from ..exceptions import NotFoundException, BadRequestException
from ..models.models import Event, User
from ..schemas.event import EventOut, EventUpdate
from ..supabase import supabase_storage
from ..uploads import read_gallery_file

router = APIRouter(prefix="/api/v1/events", tags=["events"])

EVENTS_BUCKET = "media"

KNOWN_GROUP_SLUGS = {
    "canyon-county-symphony",
    "youth-orchestra",
    "canyon-county-master-chorale",
    "canyon-winds",
    "canyon-county-flute-choir",
    "canyon-county-childrens-chorus",
    "macc",
}


def _object_path_from_public_url(url: str | None, bucket: str) -> str | None:
    if not url:
        return None
    marker = f"/object/public/{bucket}/"
    if marker not in url:
        return None
    return url.split(marker, 1)[1].split("?")[0]


def _parse_dt(value: str | None, label: str, required: bool = False) -> datetime | None:
    if value is None or value.strip() == "":
        if required:
            raise BadRequestException(f"{label} is required")
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        raise BadRequestException(f"Invalid {label}. Use ISO datetime.")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _validate_slug(slug: str) -> str:
    cleaned = slug.strip()
    if cleaned not in KNOWN_GROUP_SLUGS:
        raise BadRequestException(
            f"Unknown group. Allowed: {', '.join(sorted(KNOWN_GROUP_SLUGS))}"
        )
    return cleaned


async def _upload_poster(file: UploadFile) -> str:
    file_bytes, _media_type = await read_gallery_file(file)
    ext = Path(file.filename or "").suffix.lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise BadRequestException("Poster must be a JPG, PNG, or WEBP image")
    object_path = f"events/{uuid.uuid4().hex}{ext}"
    await supabase_storage.upload_file(
        bucket=EVENTS_BUCKET,
        file_path=object_path,
        file_bytes=file_bytes,
        content_type=file.content_type or "image/jpeg",
    )
    return supabase_storage.get_public_url(EVENTS_BUCKET, object_path)


async def _delete_poster(image_url: str | None) -> None:
    object_path = _object_path_from_public_url(image_url, EVENTS_BUCKET)
    if not object_path:
        return
    try:
        await supabase_storage.delete_file(EVENTS_BUCKET, object_path)
    except Exception:
        pass


@router.get("/", response_model=list[EventOut])
async def list_published_events(
    db: AsyncSession = Depends(get_db),
    group_slug: str | None = None,
    limit: int = 50,
):
    query = (
        select(Event)
        .where(Event.is_published.is_(True))
        .order_by(Event.starts_at.asc())
        .limit(limit)
    )
    if group_slug:
        query = query.where(Event.group_slug == group_slug.strip())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/admin", response_model=list[EventOut])
async def list_all_events(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(select(Event).order_by(Event.starts_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    title: str = Form(...),
    description: str | None = Form(None),
    location: str | None = Form(None),
    price: str | None = Form(None),
    starts_at: str = Form(...),
    ends_at: str | None = Form(None),
    group_slug: str = Form(...),
    is_published: bool = Form(False),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    start = _parse_dt(starts_at, "start time", required=True)
    end = _parse_dt(ends_at, "end time")
    if end and start and end < start:
        raise BadRequestException("End time must be after start time")

    image_url = None
    if file is not None and file.filename:
        image_url = await _upload_poster(file)

    item = Event(
        title=title.strip(),
        description=description.strip() if description else None,
        location=location.strip() if location else None,
        price=price.strip() if price else None,
        starts_at=start,
        ends_at=end,
        group_slug=_validate_slug(group_slug),
        image_url=image_url,
        is_published=is_published,
        created_by=admin.id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/{event_id}", response_model=EventOut)
async def update_event(
    event_id: int,
    payload: EventUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Event not found")

    data = payload.model_dump(exclude_unset=True)
    if "title" in data and data["title"] is not None:
        data["title"] = data["title"].strip()
    if "description" in data and data["description"] is not None:
        data["description"] = data["description"].strip() or None
    if "location" in data and data["location"] is not None:
        data["location"] = data["location"].strip() or None
    if "price" in data and data["price"] is not None:
        data["price"] = data["price"].strip() or None
    if "group_slug" in data and data["group_slug"] is not None:
        data["group_slug"] = _validate_slug(data["group_slug"])

    start = data.get("starts_at", item.starts_at)
    end = data.get("ends_at", item.ends_at)
    if end and start and end < start:
        raise BadRequestException("End time must be after start time")

    for key, value in data.items():
        setattr(item, key, value)

    await db.commit()
    await db.refresh(item)
    return item


@router.post("/{event_id}/poster", response_model=EventOut)
async def replace_event_poster(
    event_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Event not found")

    new_url = await _upload_poster(file)
    await _delete_poster(item.image_url)
    item.image_url = new_url
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException("Event not found")

    await _delete_poster(item.image_url)
    await db.delete(item)
    await db.commit()
    return None