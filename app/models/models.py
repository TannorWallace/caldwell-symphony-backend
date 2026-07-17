from __future__ import annotations

from enum import Enum
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
from datetime import datetime
from typing import Optional


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


# ==================== USER MODEL ====================
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    media: Mapped[list["Media"]] = relationship("Media", back_populates="user", cascade="all, delete-orphan")


# ==================== COMMENT MODEL (with threaded replies) ====================
class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="comments")

    media_id: Mapped[int] = mapped_column(Integer, ForeignKey("media.id"), nullable=False)
    media: Mapped["Media"] = relationship("Media", back_populates="comments")

    # Threaded replies
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("comments.id"), nullable=True)
    parent: Mapped["Comment | None"] = relationship("Comment", remote_side=[id], back_populates="replies")
    replies: Mapped[list["Comment"]] = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")

    # Admin moderation
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ==================== MEDIA MODEL ====================
class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    media_type: Mapped[str] = mapped_column(String(10), nullable=False)

    # Supabase Storage fields
    bucket: Mapped[str] = mapped_column(String(100), nullable=False, default="media")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    public_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # Extra metadata
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Who uploaded this media
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="media")

    # Link to Performance (this media belongs to a performance)
    performance_id: Mapped[Optional[int]] = mapped_column(ForeignKey("performances.id"), nullable=True)
    performance: Mapped["Performance | None"] = relationship(
        "Performance",
        back_populates="media",
        foreign_keys="[Media.performance_id]"   # ← Explicit foreign key
    )

    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="media",
        cascade="all, delete-orphan"
    )


# ==================== PERFORMANCE MODEL ====================
class Performance(Base):
    __tablename__ = "performances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cover image is now linked via media table
    cover_media_id: Mapped[Optional[int]] = mapped_column(ForeignKey("media.id"), nullable=True)
    cover_media: Mapped["Media | None"] = relationship(
        "Media",
        foreign_keys="[Performance.cover_media_id]"
    )

    is_published: Mapped[bool] = mapped_column(Boolean, default=True)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    creator: Mapped["User"] = relationship("User")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # All media items belonging to this performance
    media: Mapped[list["Media"]] = relationship(
        "Media",
        back_populates="performance",
        cascade="all, delete-orphan",
        foreign_keys="[Media.performance_id]"   # ← FIXED: Explicit foreign key
    )