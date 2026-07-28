from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class SheetMusicPieceBase(BaseModel):
    title: str
    description: Optional[str] = None


class SheetMusicPieceCreate(SheetMusicPieceBase):
    is_published: bool = False


class SheetMusicPieceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_published: Optional[bool] = None


class SheetMusicPiece(SheetMusicPieceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_published: bool
    created_at: datetime
    parts: List["SheetMusicPart"] = []


class SheetMusicPartBase(BaseModel):
    instrument: str
    title: Optional[str] = None
    piece_id: int


class SheetMusicPartCreate(SheetMusicPartBase):
    pass


class SheetMusicPartUpdate(BaseModel):
    instrument: Optional[str] = None
    title: Optional[str] = None


class SheetMusicPart(SheetMusicPartBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bucket: str
    file_path: str
    public_url: str
    file_name: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    uploaded_by: int
    created_at: datetime


SheetMusicPiece.model_rebuild()