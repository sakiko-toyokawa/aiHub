from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class SourceBase(BaseModel):
    platform: str
    name: str
    url_pattern: Optional[str] = None
    is_active: bool = True
    config: Dict[str, Any] = {}


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    platform: Optional[str] = None
    name: Optional[str] = None
    url_pattern: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class Source(SourceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
