from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
import httpx

from ..database import get_db
from ..models.models import (
    SheetMusicPiece as PieceModel,
    SheetMusicPart as PartModel,
    User as UserModel,
)
from ..schemas.sheet_music import (
    SheetMusicPiece,
    SheetMusicPieceCreate,
    SheetMusicPieceUpdate,
    SheetMusicPart,
)
from ..dependencies import get_current_admin_user, get_current_member_user
from ..exceptions import NotFoundException, BadRequestException
from ..supabase import SupabaseStorage

router = APIRouter(
    prefix="/api/v1/sheet-music",
    tags=["Sheet Music"]
)

supabase_storage = SupabaseStorage()


def _piece_to_dict(piece: PieceModel, parts: list | None = None) -> dict:
    part_list = parts if parts is not None else (piece.parts or [])
    return {
        "id": piece.id,
        "title": piece.title,
        "description": piece.description,
        "is_published": piece.is_published,
        "created_at": piece.created_at,
        "parts": [
            {
                "id": p.id,
                "instrument": p.instrument,
                "title": p.title,
                "public_url": p.public_url,
                "file_name": p.file_name,
                "file_size": p.file_size,
                "content_type": p.content_type,
                "piece_id": p.piece_id,
                "uploaded_by": p.uploaded_by,
                "created_at": p.created_at,
                "bucket": p.bucket,
                "file_path": p.file_path,
            }
            for p in part_list
        ],
    }


@router.get("/pieces", response_model=List[SheetMusicPiece])
async def list_pieces(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_member_user),
):
    """Members: published only. Admins: all."""
    query = (
        select(PieceModel)
        .options(selectinload(PieceModel.parts))
        .order_by(PieceModel.created_at.desc())
    )
    if not current_user.is_admin:
        query = query.where(PieceModel.is_published == True)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/pieces", response_model=SheetMusicPiece, status_code=status.HTTP_201_CREATED)
async def create_piece(
    piece_in: SheetMusicPieceCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user),
):
    data = piece_in.model_dump()
    data["is_published"] = False
    db_piece = PieceModel(**data)
    db.add(db_piece)
    await db.commit()
    await db.refresh(db_piece)
    return _piece_to_dict(db_piece, parts=[])


@router.post("/pieces/with-parts", status_code=status.HTTP_201_CREATED)
async def create_piece_with_parts(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    instruments: List[str] = Form(...),
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user),
):
    if len(files) != len(instruments):
        raise BadRequestException("Number of files must match number of instruments")

    db_piece = PieceModel(
        title=title.strip(),
        description=description,
        is_published=False,
    )
    db.add(db_piece)
    await db.flush()

    uploaded_parts = []
    for file, instrument in zip(files, instruments):
        file_ext = file.filename.split(".")[-1] if file.filename else "pdf"
        file_path = f"sheet-music/{db_piece.id}/{uuid.uuid4()}.{file_ext}"
        file_bytes = await file.read()

        try:
            await supabase_storage.upload_file(
                bucket="sheet-music",
                file_path=file_path,
                file_bytes=file_bytes,
                content_type=file.content_type or "application/pdf",
            )
        except Exception as e:
            raise BadRequestException(f"Failed to upload {file.filename}: {str(e)}")

        public_url = supabase_storage.get_public_url("sheet-music", file_path)

        db_part = PartModel(
            instrument=instrument.strip(),
            title=None,
            bucket="sheet-music",
            file_path=file_path,
            public_url=public_url,
            file_name=file.filename or f"part.{file_ext}",
            file_size=len(file_bytes),
            content_type=file.content_type,
            piece_id=db_piece.id,
            uploaded_by=current_admin.id,
        )
        db.add(db_part)
        uploaded_parts.append(db_part)

    await db.commit()
    await db.refresh(db_piece)
    for part in uploaded_parts:
        await db.refresh(part)

    return _piece_to_dict(db_piece, parts=uploaded_parts)


@router.put("/pieces/{piece_id}", response_model=SheetMusicPiece)
async def update_piece(
    piece_id: int,
    piece_in: SheetMusicPieceUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user),
):
    result = await db.execute(
        select(PieceModel)
        .options(selectinload(PieceModel.parts))
        .where(PieceModel.id == piece_id)
    )
    piece = result.scalar_one_or_none()
    if not piece:
        raise NotFoundException("Piece not found")

    for field, value in piece_in.model_dump(exclude_unset=True).items():
        setattr(piece, field, value)

    await db.commit()
    await db.refresh(piece)
    return piece


@router.delete("/pieces/{piece_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_piece(
    piece_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user),
):
    result = await db.execute(select(PieceModel).where(PieceModel.id == piece_id))
    piece = result.scalar_one_or_none()
    if not piece:
        raise NotFoundException("Piece not found")
    await db.delete(piece)
    await db.commit()
    return None


@router.post("/parts", response_model=SheetMusicPart, status_code=status.HTTP_201_CREATED)
async def upload_part(
    file: UploadFile = File(...),
    instrument: str = Form(...),
    piece_id: int = Form(...),
    title: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user),
):
    piece_result = await db.execute(select(PieceModel).where(PieceModel.id == piece_id))
    if not piece_result.scalar_one_or_none():
        raise NotFoundException("Piece not found")

    file_ext = file.filename.split(".")[-1] if file.filename else "pdf"
    file_path = f"sheet-music/{piece_id}/{uuid.uuid4()}.{file_ext}"
    file_bytes = await file.read()

    try:
        await supabase_storage.upload_file(
            bucket="sheet-music",
            file_path=file_path,
            file_bytes=file_bytes,
            content_type=file.content_type or "application/pdf",
        )
    except Exception as e:
        raise BadRequestException(f"Supabase upload failed: {str(e)}")

    public_url = supabase_storage.get_public_url("sheet-music", file_path)

    db_part = PartModel(
        instrument=instrument.strip(),
        title=title,
        bucket="sheet-music",
        file_path=file_path,
        public_url=public_url,
        file_name=file.filename or f"part.{file_ext}",
        file_size=len(file_bytes),
        content_type=file.content_type,
        piece_id=piece_id,
        uploaded_by=current_admin.id,
    )
    db.add(db_part)
    await db.commit()
    await db.refresh(db_part)
    return db_part


@router.delete("/parts/{part_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_part(
    part_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user),
):
    result = await db.execute(select(PartModel).where(PartModel.id == part_id))
    part = result.scalar_one_or_none()
    if not part:
        raise NotFoundException("Part not found")
    await db.delete(part)
    await db.commit()
    return None


@router.get("/parts/{part_id}/download")
async def download_part(
    part_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_member_user),
):
    """
    Stream PDF with Content-Disposition: attachment.
    Reliable on iOS Safari and Android Chrome.
    Members: published pieces only. Admins: all.
    """
    result = await db.execute(
        select(PartModel)
        .options(selectinload(PartModel.piece))
        .where(PartModel.id == part_id)
    )
    part = result.scalar_one_or_none()
    if not part:
        raise NotFoundException("Part not found")

    if not current_user.is_admin and not part.piece.is_published:
        raise NotFoundException("Part not found")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            file_res = await client.get(part.public_url)
            file_res.raise_for_status()
            content = file_res.content
    except Exception as e:
        raise BadRequestException(f"Could not fetch file: {str(e)}")

    filename = part.file_name or f"{part.instrument}.pdf"
    safe_name = filename.replace('"', "").replace("\n", " ").replace("\r", " ")

    return Response(
        content=content,
        media_type=part.content_type or "application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"',
            "Content-Length": str(len(content)),
        },
    )