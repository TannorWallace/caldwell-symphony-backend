from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .database import get_db
from .models.models import User as UserModel
from .config import settings
from .exceptions import UnauthorizedException, ForbiddenException, BadRequestException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserModel:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise UnauthorizedException("Could not validate credentials")
    except JWTError:
        raise UnauthorizedException("Could not validate credentials")

    result = await db.execute(select(UserModel).where(UserModel.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedException("Could not validate credentials")
    return user


async def get_current_active_user(current_user: UserModel = Depends(get_current_user)):
    if not current_user.is_active:
        raise BadRequestException("Inactive user")
    return current_user


async def get_current_admin_user(current_user: UserModel = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise ForbiddenException("Not enough permissions - Admin only")
    return current_user