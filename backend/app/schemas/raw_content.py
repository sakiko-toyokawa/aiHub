from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class RawContentBase(BaseModel):
    source_id: Optional[int] = None
    platform: str
    external_id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    author_url: Optional[str] = None
    url: str
    raw_data: Optional[Dict[str, Any]] = None


class RawContentCreate(RawContentBase):
    pass


class RawContentUpdate(BaseModel):
    source_id: Optional[int] = None
    platform: Optional[str] = None
    external_id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    author_url: Optional[str] = None
    url: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class RawContent(RawContentBase):
    id: int
    fetched_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
