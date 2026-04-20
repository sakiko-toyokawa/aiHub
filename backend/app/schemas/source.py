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

    # 增量抓取追踪字段
    last_fetched_at: Optional[datetime] = None
    last_item_id: Optional[str] = None
    fetch_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None

    class Config:
        from_attributes = True
