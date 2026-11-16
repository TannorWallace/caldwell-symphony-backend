from __future__ import annotations

from enum import Enum
from datetime import date, time, datetime
from typing import Optional

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, Date, Time, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

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
    is_member: Mapped[bool] = mapped_column(Boolean, default=False)
    reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="user", cascade="all, delete-orphan"
    )
    media: Mapped[list["Media"]] = relationship(
        "Media", back_populates="user", cascade="all, delete-orphan"
    )
    member_messages: Mapped[list["MemberMessage"]] = relationship(
        "MemberMessage", back_populates="user", cascade="all, delete-orphan"
    )
    ensembles: Mapped[list["UserEnsemble"]] = relationship(
        "UserEnsemble", back_populates="user", cascade="all, delete-orphan"
    )


class UserEnsemble(Base):
    __tablename__ = "user_ensembles"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    group_slug: Mapped[str] = mapped_column(String(100), primary_key=True)

    user: Mapped["User"] = relationship("User", back_populates="ensembles")


# ==================== COMMENT MODEL ====================
class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="comments")

    media_id: Mapped[int] = mapped_column(Integer, ForeignKey("media.id"), nullable=False)
    media: Mapped["Media"] = relationship("Media", back_populates="comments")

    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("comments.id"), nullable=True)
    parent: Mapped["Comment | None"] = relationship(
        "Comment", remote_side=[id], back_populates="replies"
    )
    replies: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="parent", cascade="all, delete-orphan"
    )

    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ==================== MEDIA MODEL ====================
class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    media_type: Mapped[str] = mapped_column(String(10), nullable=False)

    bucket: Mapped[str] = mapped_column(String(100), nullable=False, default="media")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    public_url: Mapped[str] = mapped_column(String(500), nullable=False)

    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="media")

    performance_id: Mapped[Optional[int]] = mapped_column(ForeignKey("performances.id"), nullable=True)
    performance: Mapped["Performance | None"] = relationship(
        "Performance",
        back_populates="media",
        foreign_keys="[Media.performance_id]"
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

    cover_media_id: Mapped[Optional[int]] = mapped_column(ForeignKey("media.id"), nullable=True)
    cover_media: Mapped["Media | None"] = relationship(
        "Media",
        foreign_keys="[Performance.cover_media_id]"
    )

    is_published: Mapped[bool] = mapped_column(Boolean, default=True)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    creator: Mapped["User"] = relationship("User")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    media: Mapped[list["Media"]] = relationship(
        "Media",
        back_populates="performance",
        cascade="all, delete-orphan",
        foreign_keys="[Media.performance_id]"
    )


# ==================== MEMBER MESSAGE MODEL ====================
class MemberMessage(Base):
    __tablename__ = "member_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="member_messages")

    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("member_messages.id"), nullable=True
    )
    parent: Mapped["MemberMessage | None"] = relationship(
        "MemberMessage",
        remote_side=[id],
        back_populates="replies"
    )
    replies: Mapped[list["MemberMessage"]] = relationship(
        "MemberMessage",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    group_slug = Column(String(100), nullable=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ==================== SHEET MUSIC MODELS ====================

class SheetMusicPiece(Base):
    """Standalone sheet music package. Not tied to public performances."""
    __tablename__ = "sheet_music_pieces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    group_slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    parts: Mapped[list["SheetMusicPart"]] = relationship(
        "SheetMusicPart",
        back_populates="piece",
        cascade="all, delete-orphan"
    )

class SheetMusicPart(Base):
    """Individual instrument PDF for a piece."""
    __tablename__ = "sheet_music_parts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    instrument: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    bucket: Mapped[str] = mapped_column(String(100), nullable=False, default="sheet-music")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    public_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    piece_id: Mapped[int] = mapped_column(ForeignKey("sheet_music_pieces.id"), nullable=False)
    piece: Mapped["SheetMusicPiece"] = relationship("SheetMusicPiece", back_populates="parts")

    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    uploader: Mapped["User"] = relationship("User")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


#====================================ANNOUNCEMENTS============================================

class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    group_slug = Column(String(100), nullable=True, index=True)
    creator: Mapped["User | None"] = relationship("User")


#====================================EVENTS============================================

class Event(Base):
    """Public concert / group event listing (not the performance gallery)."""
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    price: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    group_slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    creator: Mapped["User | None"] = relationship("User")


#=================================SPOTLIGHTS============================================
class Spotlight(Base):
    __tablename__ = "spotlights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    guidelines_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    registration_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class RecurringSchedule(Base):
    """Repeating weekly schedule rule per ensemble (e.g. every Thursday 7–9pm)."""
    __tablename__ = "recurring_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday ... 6=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    recurrence_start: Mapped[date] = mapped_column(Date, nullable=False)
    recurrence_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # null = ongoing

    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    creator: Mapped["User | None"] = relationship("User")
    exceptions: Mapped[list["ScheduleException"]] = relationship(
        "ScheduleException", back_populates="recurring_schedule", cascade="all, delete-orphan"
    )


class ScheduleException(Base):
    """Individual date exception for a recurring schedule (cancel or later override)."""
    __tablename__ = "schedule_exceptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recurring_schedule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recurring_schedules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exception_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    recurring_schedule: Mapped["RecurringSchedule"] = relationship(
        "RecurringSchedule", back_populates="exceptions"
    )