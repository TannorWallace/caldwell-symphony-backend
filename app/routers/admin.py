from fastapi import APIRouter, Depends, Path, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
import uuid

from ..dependencies import get_current_admin_user
from ..database import get_db
from ..models.models import (
    User as UserModel, 
    Comment as CommentModel, 
    Performance as PerformanceModel,
    Media as MediaModel
)
from ..schemas.user import UserCreate, User
from ..schemas.performance import Performance, PerformanceCreate, PerformanceUpdate
from ..routers.users import get_password_hash
from ..exceptions import NotFoundException, BadRequestException
from ..supabase import SupabaseStorage

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"]
)

supabase_storage = SupabaseStorage()


# ==================== TEMPORARY BOOTSTRAP ENDPOINT ====================
@router.post("/bootstrap-first-admin", response_model=User, status_code=status.HTTP_201_CREATED)
async def bootstrap_first_admin(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserModel).where(UserModel.is_admin == True))
    if result.scalar_one_or_none():
        raise BadRequestException("An admin user already exists.")

    result = await db.execute(
        select(UserModel).where(
            (UserModel.email == user_in.email) | (UserModel.username == user_in.username)
        )
    )
    if result.scalar_one_or_none():
        raise BadRequestException("Email or username already registered")

    hashed_password = get_password_hash(user_in.password)

    db_user = UserModel(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=True
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


# ==================== USER MANAGEMENT ====================
@router.get("/users", response_model=List[User])
async def list_all_users(
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    result = await db.execute(select(UserModel))
    return result.scalars().all()


@router.get("/users/{user_id}", response_model=User)
async def get_user_by_id(
    user_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")
    return user


@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    user.email = user_in.email
    user.username = user_in.username
    if user_in.password:
        user.hashed_password = get_password_hash(user_in.password)

    await db.commit()
    await db.refresh(user)
    return user


@router.post("/users/{user_id}/promote")
async def promote_to_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")
    if user.is_admin:
        raise BadRequestException("User is already an admin")

    user.is_admin = True
    await db.commit()
    return {"message": "User has been promoted to admin"}


@router.post("/users/{user_id}/demote")
async def demote_from_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")
    if not user.is_admin:
        raise BadRequestException("User is not an admin")

    user.is_admin = False
    await db.commit()
    return {"message": "User has been demoted"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    await db.delete(user)
    await db.commit()
    return {"message": f"User {user_id} has been deleted"}


# ==================== ADMIN COMMENT HARD DELETE WITH CASCADE ====================
@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """Permanently delete a comment AND all its replies (hard delete with cascade)"""
    result = await db.execute(select(CommentModel).where(CommentModel.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise NotFoundException("Comment not found")

    # Collect all descendant reply IDs
    ids_to_delete = [comment_id]
    to_check = [comment_id]

    while to_check:
        current = to_check.pop()
        child_result = await db.execute(
            select(CommentModel.id).where(CommentModel.parent_id == current)
        )
        children = child_result.scalars().all()
        for child_id in children:
            ids_to_delete.append(child_id)
            to_check.append(child_id)

    await db.execute(
        delete(CommentModel).where(CommentModel.id.in_(ids_to_delete))
    )
    await db.commit()

    return {"message": f"Comment {comment_id} and all {len(ids_to_delete)-1} replies have been permanently deleted"}


# ==================== PERFORMANCE MANAGEMENT (Admin Only) ====================

@router.post("/performances", response_model=Performance, status_code=status.HTTP_201_CREATED)
async def create_performance(
    performance_in: PerformanceCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """Admin creates a new performance"""
    db_performance = PerformanceModel(
        **performance_in.model_dump(),
        created_by=current_admin.id
    )
    db.add(db_performance)
    await db.commit()
    await db.refresh(db_performance)
    return db_performance


@router.put("/performances/{performance_id}", response_model=Performance)
async def update_performance(
    performance_id: int,
    performance_in: PerformanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """Admin updates a performance"""
    result = await db.execute(select(PerformanceModel).where(PerformanceModel.id == performance_id))
    performance = result.scalar_one_or_none()
    if not performance:
        raise NotFoundException("Performance not found")

    update_data = performance_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(performance, field, value)

    await db.commit()
    await db.refresh(performance)
    return performance


@router.delete("/performances/{performance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_performance(
    performance_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """Admin deletes a performance"""
    result = await db.execute(select(PerformanceModel).where(PerformanceModel.id == performance_id))
    performance = result.scalar_one_or_none()
    if not performance:
        raise NotFoundException("Performance not found")

    await db.delete(performance)
    await db.commit()
    return None


# ==================== ADMIN MEDIA UPLOAD (Supabase) ====================

@router.post("/media", status_code=status.HTTP_201_CREATED)
async def upload_single_media(
    file: UploadFile = File(...),
    title: str = Form(None),
    performance_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """Admin uploads a single image to Supabase and links it to a performance"""

    # Check if performance exists
    perf_result = await db.execute(
        select(PerformanceModel).where(PerformanceModel.id == performance_id)
    )
    if not perf_result.scalar_one_or_none():
        raise NotFoundException("Performance not found")

    # Generate unique file path
    file_ext = file.filename.split(".")[-1] if file.filename else "jpg"
    file_path = f"performances/{performance_id}/{uuid.uuid4()}.{file_ext}"

    file_bytes = await file.read()

    try:
        await supabase_storage.upload_file(
            bucket="media",
            file_path=file_path,
            file_bytes=file_bytes,
            content_type=file.content_type or "image/jpeg"
        )
    except Exception as e:
        raise BadRequestException(f"Supabase upload failed: {str(e)}")

    public_url = supabase_storage.get_public_url("media", file_path)

    # Save to database
    db_media = MediaModel(
        media_type="image",
        bucket="media",
        file_path=file_path,
        public_url=public_url,
        title=title or file.filename,
        user_id=current_admin.id,
        performance_id=performance_id
    )

    db.add(db_media)
    await db.commit()
    await db.refresh(db_media)

    return {"message": "Image uploaded successfully", "media_id": db_media.id}


@router.post("/media/bulk", status_code=status.HTTP_201_CREATED)
async def upload_multiple_media(
    files: List[UploadFile] = File(...),
    title: str = Form(None),
    performance_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_admin_user)
):
    """Admin uploads multiple images to Supabase and links them to a performance"""

    # Check if performance exists
    perf_result = await db.execute(
        select(PerformanceModel).where(PerformanceModel.id == performance_id)
    )
    if not perf_result.scalar_one_or_none():
        raise NotFoundException("Performance not found")

    uploaded_count = 0

    for file in files:
        file_ext = file.filename.split(".")[-1] if file.filename else "jpg"
        file_path = f"performances/{performance_id}/{uuid.uuid4()}.{file_ext}"

        file_bytes = await file.read()

        try:
            await supabase_storage.upload_file(
                bucket="media",
                file_path=file_path,
                file_bytes=file_bytes,
                content_type=file.content_type or "image/jpeg"
            )
        except Exception as e:
            raise BadRequestException(f"Failed to upload {file.filename}: {str(e)}")

        public_url = supabase_storage.get_public_url("media", file_path)

        db_media = MediaModel(
            media_type="image",
            bucket="media",
            file_path=file_path,
            public_url=public_url,
            title=title or file.filename,
            user_id=current_admin.id,
            performance_id=performance_id
        )

        db.add(db_media)
        uploaded_count += 1

    await db.commit()

    return {
        "message": f"Successfully uploaded {uploaded_count} images",
        "performance_id": performance_id
    }