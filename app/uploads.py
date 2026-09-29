from pathlib import Path

from fastapi import UploadFile

from .exceptions import BadRequestException

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm"}
ALLOWED_GALLERY_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES
ALLOWED_PDF_TYPES = {"application/pdf"}
ALLOWED_FLYER_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_PDF_TYPES

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_VIDEO_BYTES = 50 * 1024 * 1024
MAX_PDF_BYTES = 20 * 1024 * 1024
MAX_FLYER_BYTES = 10 * 1024 * 1024

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".webm"}
PDF_EXTENSIONS = {".pdf"}


def _extension(filename: str | None) -> str:
    return Path(filename or "").suffix.lower()


def media_type_from_content(content_type: str | None, filename: str | None = None) -> str:
    if content_type and content_type.startswith("video/"):
        return "video"
    if _extension(filename) in VIDEO_EXTENSIONS:
        return "video"
    return "image"


def _looks_like_pdf(data: bytes) -> bool:
    return data[:5] == b"%PDF-"


def _looks_like_jpeg(data: bytes) -> bool:
    return data[:3] == b"\xff\xd8\xff"


def _looks_like_png(data: bytes) -> bool:
    return data[:8] == b"\x89PNG\r\n\x1a\n"


def _looks_like_webp(data: bytes) -> bool:
    return data[:4] == b"RIFF" and data[8:12] == b"WEBP"


def _looks_like_mp4(data: bytes) -> bool:
    return len(data) >= 12 and data[4:8] == b"ftyp"


def _looks_like_webm(data: bytes) -> bool:
    return data[:4] == b"\x1a\x45\xdf\xa3"


def _validate_magic(data: bytes, ext: str, label: str) -> None:
    ok = False
    if ext == ".pdf":
        ok = _looks_like_pdf(data)
    elif ext in {".jpg", ".jpeg"}:
        ok = _looks_like_jpeg(data)
    elif ext == ".png":
        ok = _looks_like_png(data)
    elif ext == ".webp":
        ok = _looks_like_webp(data)
    elif ext == ".mp4":
        ok = _looks_like_mp4(data)
    elif ext == ".webm":
        ok = _looks_like_webm(data)

    if not ok:
        raise BadRequestException(f"{label.capitalize()} contents do not match the file type")


async def read_validated_upload(
    file: UploadFile,
    *,
    allowed_types: set[str],
    allowed_exts: set[str],
    max_bytes: int,
    label: str = "file",
) -> bytes:
    if not file.filename:
        raise BadRequestException(f"Missing {label} filename")

    ext = _extension(file.filename)
    if ext not in allowed_exts:
        raise BadRequestException(
            f"Unsupported {label} type. Allowed extensions: {', '.join(sorted(allowed_exts))}"
        )

    content_type = (file.content_type or "").lower()
    if content_type and content_type not in allowed_types:
        raise BadRequestException(
            f"Unsupported {label} type. Allowed: {', '.join(sorted(allowed_types))}"
        )

    data = await file.read()
    if not data:
        raise BadRequestException(f"{label.capitalize()} is empty")
    if len(data) > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        raise BadRequestException(f"{label.capitalize()} is too large. Max {max_mb:.0f} MB")

    _validate_magic(data, ext, label)
    return data


async def read_gallery_file(file: UploadFile) -> tuple[bytes, str]:
    data = await read_validated_upload(
        file,
        allowed_types=ALLOWED_GALLERY_TYPES,
        allowed_exts=IMAGE_EXTENSIONS | VIDEO_EXTENSIONS,
        max_bytes=MAX_VIDEO_BYTES,
        label="media",
    )
    if _extension(file.filename) in IMAGE_EXTENSIONS and len(data) > MAX_IMAGE_BYTES:
        raise BadRequestException("Image is too large. Max 10 MB")
    return data, media_type_from_content(file.content_type, file.filename)


async def read_pdf_file(file: UploadFile) -> bytes:
    return await read_validated_upload(
        file,
        allowed_types=ALLOWED_PDF_TYPES,
        allowed_exts=PDF_EXTENSIONS,
        max_bytes=MAX_PDF_BYTES,
        label="PDF",
    )


async def read_flyer_file(file: UploadFile) -> bytes:
    return await read_validated_upload(
        file,
        allowed_types=ALLOWED_FLYER_TYPES,
        allowed_exts=IMAGE_EXTENSIONS | PDF_EXTENSIONS,
        max_bytes=MAX_FLYER_BYTES,
        label="flyer",
    )