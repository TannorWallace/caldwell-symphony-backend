from jose import jwt
from sqlalchemy import select
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..config import settings
from ..models.models import User as UserModel, Comment as CommentModel, Media as MediaModel
from ..schemas.user import UserCreate, User, Token, UserDelete, UserActivity
from ..schemas.comment import Comment
from ..schemas.media import Media
from ..dependencies import get_current_active_user


router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ==================== REGISTER REGULAR USER ====================
@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserModel).where(
            (UserModel.email == user_in.email) | (UserModel.username == user_in.username)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email or username already registered")

    hashed_password = get_password_hash(user_in.password)

    db_user = UserModel(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


# ==================== LOGIN ====================
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UserModel).where(UserModel.username == form_data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(
        data={"sub": user.username, "is_admin": user.is_admin}
    )

    return {"access_token": access_token, "token_type": "bearer"}


# ==================== PROTECTED ROUTES ====================
@router.get("/profile", response_model=User)
async def get_current_user_profile(current_user: UserModel = Depends(get_current_active_user)):
    return current_user


# ==================== MY ACTIVITY (NO /me/) ====================
@router.get("/activity", response_model=UserActivity)
async def get_my_activity(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """Returns user's recent comments and all their uploaded media"""
    
    # Recent comments (last 10)
    comments_result = await db.execute(
        select(CommentModel)
        .options(selectinload(CommentModel.user))
        .where(CommentModel.user_id == current_user.id, CommentModel.is_deleted == False)
        .order_by(CommentModel.created_at.desc())
        .limit(10)
    )
    recent_comments = comments_result.scalars().all()

    # Manually attach username (fixes null username issue)
    for comment in recent_comments:
        if comment.user:
            comment.username = comment.user.username

    # All media uploaded by this user
    media_result = await db.execute(
        select(MediaModel)
        .where(MediaModel.user_id == current_user.id)
        .order_by(MediaModel.created_at.desc())
    )
    my_media = media_result.scalars().all()

    return {
        "total_comments": len(recent_comments),
        "total_media": len(my_media),
        "recent_comments": recent_comments,
        "my_media": my_media
    }


# ==================== UPDATE OWN PROFILE ====================
@router.put("/profile", response_model=User)
async def update_own_profile(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    result = await db.execute(
        select(UserModel).where(
            (UserModel.id != current_user.id) & 
            ((UserModel.email == user_in.email) | (UserModel.username == user_in.username))
        )
    )
    if result.scalar_one_or_none():
        await db.rollback()
        raise HTTPException(status_code=400, detail="Email or username already taken")

    current_user.email = user_in.email
    current_user.username = user_in.username

    if user_in.password:
        current_user.hashed_password = get_password_hash(user_in.password)

    await db.commit()
    await db.refresh(current_user)
    return current_user


# ==================== DELETE OWN ACCOUNT ====================
@router.delete("/profile")
async def delete_own_account(
    delete_data: UserDelete,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    if not verify_password(delete_data.password, current_user.hashed_password):
        await db.rollback()
        raise HTTPException(status_code=401, detail="Incorrect password")

    await db.delete(current_user)
    await db.commit()

    return {"message": "Your account has been successfully deleted."}